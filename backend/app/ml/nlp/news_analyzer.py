import re
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging
from app.ml.nlp.finbert import analyze_with_finbert, analyze_batch_finbert

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Financial keyword boosters for Indian market
# ---------------------------------------------------------------------------
INDIAN_BULLISH_KEYWORDS = [
    "rally", "surge", "gains", "bullish", "outperform", "upgrade",
    "growth", "profit", "beat", "record", "strong", "positive",
    "recovery", "rebound", "breakout", "buy", "accumulate",
    "nifty high", "sensex high", "fii buying", "dii buying",
    "rate cut", "rbi easing", "gdp growth", "earnings beat",
    "ipo listing", "dividend", "buyback", "merger", "acquisition",
]

INDIAN_BEARISH_KEYWORDS = [
    "crash", "fall", "decline", "bearish", "underperform", "downgrade",
    "loss", "miss", "weak", "negative", "selloff", "correction",
    "recession", "inflation", "rate hike", "fii selling", "outflow",
    "nifty low", "sensex low", "default", "bankruptcy", "fraud",
    "sebi ban", "npa", "write-off", "margin call", "circuit breaker",
]

GEOPOLITICAL_RISK_KEYWORDS = [
    "war", "conflict", "crisis", "sanction", "ban", "tension",
    "iran", "israel", "russia", "ukraine", "taiwan", "china",
    "missile", "attack", "oil supply", "hormuz", "crude surge",
]

SECTOR_KEYWORDS = {
    "banking":  ["bank", "nbfc", "rbi", "interest rate", "npa", "hdfc", "sbi", "icici", "kotak"],
    "it":       ["tcs", "infosys", "wipro", "tech mahindra", "hcl", "software", "it sector", "nasdaq"],
    "pharma":   ["pharma", "drug", "fda", "cipla", "sun pharma", "dr reddy", "healthcare"],
    "auto":     ["maruti", "tata motors", "bajaj", "hero", "electric vehicle", "ev", "auto sector"],
    "energy":   ["oil", "gas", "crude", "ongc", "reliance", "solar", "power", "ntpc"],
    "fmcg":     ["hindustan unilever", "nestle", "itc", "dabur", "consumer", "fmcg"],
    "realty":   ["dlf", "real estate", "realty", "housing", "property", "oberoi"],
    "metals":   ["tata steel", "jsw", "hindalco", "vedanta", "steel", "aluminium", "copper"],
    "economy":  ["gdp", "cpi", "wpi", "rbi policy", "budget", "fiscal", "trade deficit"],
}


def preprocess_text(text: str) -> str:
    """Cleans and normalizes financial news text."""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text[:512]


def detect_sectors(text: str) -> List[str]:
    """Detects relevant sectors from article text."""
    text_lower = text.lower()
    detected   = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(sector)
    return detected if detected else ["general"]


def calculate_keyword_boost(text: str) -> float:
    """Calculates sentiment boost from financial keywords."""
    text_lower    = text.lower()
    bullish_count = sum(1 for kw in INDIAN_BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in INDIAN_BEARISH_KEYWORDS if kw in text_lower)
    geo_count     = sum(1 for kw in GEOPOLITICAL_RISK_KEYWORDS if kw in text_lower)
    boost         = (bullish_count * 0.04) - (bearish_count * 0.04) - (geo_count * 0.08)
    return float(max(-0.5, min(0.5, boost)))


def calculate_geopolitical_risk(text: str) -> Dict:
    """Calculates geopolitical risk score from text."""
    text_lower = text.lower()
    risk_count = sum(1 for kw in GEOPOLITICAL_RISK_KEYWORDS if kw in text_lower)
    risk_score = min(1.0, risk_count * 0.15)
    if risk_score > 0.6:
        level = "Critical"
        color = "red"
    elif risk_score > 0.3:
        level = "High"
        color = "orange"
    elif risk_score > 0.1:
        level = "Elevated"
        color = "yellow"
    else:
        level = "Low"
        color = "green"
    return {
        "score": round(risk_score, 3),
        "level": level,
        "color": color,
        "keywords_detected": [kw for kw in GEOPOLITICAL_RISK_KEYWORDS if kw in text_lower],
    }


def analyze_article(article: Dict, use_finbert: bool = True) -> Dict:
    """
    Analyzes a single news article using FinBERT + keyword boost.
    Combined score = FinBERT (70%) + keyword boost (30%)
    """
    title       = article.get("title", "")
    description = article.get("description", "")
    full_text   = preprocess_text(f"{title}. {description}")

    # FinBERT analysis
    if use_finbert:
        finbert_result = analyze_with_finbert(full_text)
    else:
        from app.ml.nlp.finbert import _fallback_sentiment
        finbert_result = _fallback_sentiment(full_text)

    # Keyword boost
    keyword_boost = calculate_keyword_boost(full_text)

    # Combined score (FinBERT 70% + keywords 30%)
    combined_score = (finbert_result["compound"] * 0.7) + (keyword_boost * 0.3)
    combined_score = float(max(-1.0, min(1.0, combined_score)))

    # Final sentiment label
    if combined_score >= 0.1:
        sentiment = "Positive"
        emoji     = "📈"
    elif combined_score <= -0.1:
        sentiment = "Negative"
        emoji     = "📉"
    else:
        sentiment = "Neutral"
        emoji     = "➡️"

    # Geopolitical risk
    geo_risk = calculate_geopolitical_risk(full_text)

    # Risk level
    if combined_score <= -0.4 or geo_risk["level"] in ["Critical", "High"]:
        risk_level = {"level": "High",     "color": "red",    "action": "Review portfolio exposure immediately"}
    elif combined_score <= -0.2:
        risk_level = {"level": "Elevated", "color": "orange", "action": "Monitor portfolio closely"}
    elif combined_score >= 0.3:
        risk_level = {"level": "Low",      "color": "green",  "action": "Market sentiment positive — maintain allocation"}
    else:
        risk_level = {"level": "Neutral",  "color": "gray",   "action": "No immediate action required"}

    return {
        "title":              title[:200],
        "source":             article.get("source", "Unknown"),
        "published_at":       article.get("published_at", ""),
        "sentiment":          sentiment,
        "emoji":              emoji,
        "compound_score":     round(combined_score, 4),
        "finbert_score":      finbert_result["compound"],
        "finbert_confidence": finbert_result["confidence"],
        "keyword_boost":      round(keyword_boost, 4),
        "model_used":         finbert_result["model"],
        "sectors_detected":   detect_sectors(full_text),
        "geopolitical_risk":  geo_risk,
        "risk_level":         risk_level,
    }


def analyze_all_news(
    articles: List[Dict],
    use_finbert: bool = True,
) -> Dict:
    """
    Analyzes all news articles and generates market intelligence report.
    """
    if not articles:
        return {}

    logger.info(f"Analyzing {len(articles)} articles with {'FinBERT' if use_finbert else 'VADER'}...")

    analyzed      = []
    sector_scores = {}
    geo_risk_max  = 0.0

    for article in articles:
        result = analyze_article(article, use_finbert=use_finbert)
        analyzed.append(result)

        # Aggregate sector scores
        for sector in result["sectors_detected"]:
            if sector not in sector_scores:
                sector_scores[sector] = []
            sector_scores[sector].append(result["compound_score"])

        # Track max geopolitical risk
        geo_risk_max = max(geo_risk_max, result["geopolitical_risk"]["score"])

    # Overall market sentiment
    scores     = [a["compound_score"] for a in analyzed]
    avg_score  = float(np.mean(scores))

    if avg_score >= 0.15:
        market_sentiment = "Bullish"
        market_emoji     = "🟢"
    elif avg_score <= -0.15:
        market_sentiment = "Bearish"
        market_emoji     = "🔴"
    else:
        market_sentiment = "Neutral"
        market_emoji     = "🟡"

    # Sector summary
    sector_summary = {}
    for sector, s_scores in sector_scores.items():
        avg = float(np.mean(s_scores))
        sector_summary[sector] = {
            "avg_score":  round(avg, 4),
            "sentiment":  "Positive" if avg > 0.1 else "Negative" if avg < -0.1 else "Neutral",
            "articles":   len(s_scores),
            "signal":     "OVERWEIGHT" if avg > 0.2 else "UNDERWEIGHT" if avg < -0.2 else "NEUTRAL",
        }

    # Risk alerts
    risk_alerts = [
        a for a in analyzed
        if a["risk_level"]["level"] in ["High", "Elevated"]
        or a["geopolitical_risk"]["level"] in ["Critical", "High"]
    ]

    # Overall geopolitical risk
    if geo_risk_max > 0.6:
        geo_level = "Critical"
    elif geo_risk_max > 0.3:
        geo_level = "High"
    elif geo_risk_max > 0.1:
        geo_level = "Elevated"
    else:
        geo_level = "Low"

    return {
        "total_articles":      len(analyzed),
        "overall_score":       round(avg_score, 4),
        "market_sentiment":    market_sentiment,
        "market_emoji":        market_emoji,
        "sector_sentiment":    sector_summary,
        "risk_alerts":         risk_alerts[:5],
        "total_risk_alerts":   len(risk_alerts),
        "geopolitical_risk": {
            "max_score": round(geo_risk_max, 3),
            "level":     geo_level,
        },
        "articles":            analyzed,
        "model_used":          "FinBERT" if use_finbert else "VADER",
        "analyzed_at":         datetime.now().isoformat(),
    }