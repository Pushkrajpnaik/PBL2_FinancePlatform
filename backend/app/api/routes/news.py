from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.ml.nlp.sentiment import (
    analyze_sentiment,
    analyze_news_batch,
)
from app.services.news_service import (
    fetch_live_news,
    fetch_news_for_asset,
)

router = APIRouter()


class SentimentRequest(BaseModel):
    text: str


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
    Analyze sentiment of any financial text or news headline.
    """
    return analyze_sentiment(request.text)


@router.get("/market-sentiment")
async def get_market_sentiment(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get overall market sentiment from latest news.
    """
    articles = await fetch_live_news("all")
    return analyze_news_batch(articles)


@router.get("/sector-sentiment/{sector}")
async def get_sector_sentiment(
    sector: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get sentiment for a specific sector.
    Sectors: banking, it, pharma, auto, energy, fmcg, realty, metals
    """
    articles = await fetch_news_for_asset(sector)
    result   = analyze_news_batch(articles)
    return {
        "sector":   sector,
        "sentiment": result["market_sentiment"],
        "score":    result["overall_score"],
        "articles": result["articles"],
        "risk":     result["risk_level"],
    }


@router.post("/analyze-batch")
def analyze_batch_news(
    articles: List[NewsItem],
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze sentiment of a batch of news articles.
    """
    articles_dict = [a.model_dump() for a in articles]
    return analyze_news_batch(articles_dict)


@router.get("/latest")
async def get_latest_news(
    category: str = "all",
    current_user: User = Depends(get_current_active_user),
):
    """
    Get latest financial news with sentiment scores.
    Categories: all, market, economy, sector, global, mutual_funds
    """
    articles = await fetch_live_news(category)
    results  = []
    for article in articles:
        text      = f"{article['title']} {article['description']}"
        sentiment = analyze_sentiment(text)
        results.append({
            "title":        article["title"],
            "source":       article["source"],
            "published_at": article["published_at"],
            "category":     article["category"],
            "sentiment":    sentiment["sentiment"],
            "score":        sentiment["compound_score"],
            "risk_level":   sentiment["risk_level"]["level"],
            "sectors":      sentiment["sectors_detected"],
        })

    return {
        "total":    len(results),
        "category": category,
        "news":     results,
    }


@router.get("/risk-alerts")
async def get_risk_alerts(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns only high-risk news articles that need attention.
    """
    articles = await fetch_live_news("all")
    alerts   = []

    for article in articles:
        text      = f"{article['title']} {article['description']}"
        sentiment = analyze_sentiment(text)
        if sentiment["risk_level"]["level"] in ["High", "Elevated"]:
            alerts.append({
                "title":       article["title"],
                "source":      article["source"],
                "risk_level":  sentiment["risk_level"]["level"],
                "risk_color":  sentiment["risk_level"]["color"],
                "action":      sentiment["risk_level"]["action"],
                "score":       sentiment["compound_score"],
                "sectors":     sentiment["sectors_detected"],
            })

    return {
        "total_alerts": len(alerts),
        "alerts":       alerts,
        "message":      f"{len(alerts)} risk alerts detected in latest news",
    }