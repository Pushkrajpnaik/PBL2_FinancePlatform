from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.data.ingestion.news_fetcher import (
    fetch_all_news,
    fetch_news_for_keyword,
    get_news_categories,
)
from app.ml.nlp.news_analyzer import (
    analyze_all_news,
    analyze_article,
    calculate_geopolitical_risk,
)
from app.data.processing.cache_manager import (
    get_cached_news_sentiment,
    cache_news_sentiment,
)

router = APIRouter()


class SentimentRequest(BaseModel):
    text: str
    use_finbert: bool = True


class NewsItem(BaseModel):
    title:        str
    description:  Optional[str] = ""
    source:       Optional[str] = "Unknown"
    published_at: Optional[str] = ""


@router.post("/analyze-text")
def analyze_text_sentiment(
    request: SentimentRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze sentiment of any financial text using FinBERT.
    Much more accurate than VADER for financial text.
    """
    article = {
        "title":       request.text,
        "description": "",
        "source":      "manual",
    }
    return analyze_article(article, use_finbert=request.use_finbert)


@router.get("/market-sentiment")
async def get_market_sentiment(
    use_finbert: bool = True,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get overall market sentiment from latest live news.
    Uses FinBERT for accurate financial sentiment analysis.
    """
    if not force_refresh:
        cached = get_cached_news_sentiment()
        if cached:
            cached["from_cache"] = True
            return cached

    articles = await _fetch_news()
    result   = analyze_all_news(articles, use_finbert=use_finbert)
    cache_news_sentiment(result)
    result["from_cache"] = False
    return result


@router.get("/sector-sentiment/{sector}")
async def get_sector_sentiment(
    sector: str,
    use_finbert: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get FinBERT sentiment for a specific sector.
    """
    articles = fetch_news_for_keyword(sector)
    if not articles:
        raise HTTPException(status_code=404, detail=f"No news found for sector: {sector}")
    result = analyze_all_news(articles, use_finbert=use_finbert)
    return {
        "sector":           sector,
        "sentiment":        result["market_sentiment"],
        "score":            result["overall_score"],
        "sector_summary":   result["sector_sentiment"].get(sector, {}),
        "geopolitical_risk": result["geopolitical_risk"],
        "articles":         result["articles"],
        "model_used":       result["model_used"],
    }


@router.post("/analyze-batch")
def analyze_batch_news(
    articles: List[NewsItem],
    use_finbert: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """Analyze sentiment of a batch of news articles using FinBERT."""
    articles_dict = [a.model_dump() for a in articles]
    return analyze_all_news(articles_dict, use_finbert=use_finbert)


@router.get("/latest")
async def get_latest_news(
    category: str = "all",
    use_finbert: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get latest financial news with FinBERT sentiment scores.
    """
    articles = await _fetch_news()

    if category != "all":
        categorized = get_news_categories(articles)
        articles    = categorized.get(category, articles)

    result = analyze_all_news(articles, use_finbert=use_finbert)

    return {
        "total":            result["total_articles"],
        "category":         category,
        "market_sentiment": result["market_sentiment"],
        "overall_score":    result["overall_score"],
        "model_used":       result["model_used"],
        "news":             result["articles"],
    }


@router.get("/risk-alerts")
async def get_risk_alerts(
    use_finbert: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns high-risk news articles detected by FinBERT.
    Includes geopolitical risk scoring.
    """
    articles = await _fetch_news()
    result   = analyze_all_news(articles, use_finbert=use_finbert)

    return {
        "total_alerts":      result["total_risk_alerts"],
        "alerts":            result["risk_alerts"],
        "geopolitical_risk": result["geopolitical_risk"],
        "market_sentiment":  result["market_sentiment"],
        "message":           f"{result['total_risk_alerts']} risk alerts detected by {result['model_used']}",
    }


@router.get("/geopolitical-risk")
async def get_geopolitical_risk(
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculates current geopolitical risk score from live news.
    Novel feature — not available on any Indian platform!
    """
    articles   = await _fetch_news()
    all_text   = " ".join([
        f"{a.get('title', '')} {a.get('description', '')}"
        for a in articles
    ])
    geo_risk   = calculate_geopolitical_risk(all_text)
    result     = analyze_all_news(articles[:10], use_finbert=False)

    return {
        "geopolitical_risk":  geo_risk,
        "market_sentiment":   result["market_sentiment"],
        "overall_score":      result["overall_score"],
        "top_risk_articles": [
            a for a in result["articles"]
            if a["geopolitical_risk"]["level"] in ["Critical", "High"]
        ][:5],
        "recommendation": _get_geo_recommendation(geo_risk["level"]),
    }


def _get_geo_recommendation(risk_level: str) -> str:
    recommendations = {
        "Critical": "Immediate portfolio de-risking recommended. Increase gold and debt allocation significantly.",
        "High":     "Consider reducing equity exposure by 15-20%. Increase defensive assets.",
        "Elevated": "Monitor closely. Keep 10% additional cash buffer.",
        "Low":      "Normal market conditions. Maintain current allocation.",
    }
    return recommendations.get(risk_level, "Monitor situation.")


async def _fetch_news() -> list:
    """Helper to fetch news."""
    articles = fetch_all_news(max_per_feed=8)
    return articles if articles else []