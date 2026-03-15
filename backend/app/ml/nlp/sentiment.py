import re
from typing import Dict, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ---------------------------------------------------------------------------
# VADER Sentiment Analyzer (fast, no GPU needed)
# ---------------------------------------------------------------------------
vader = SentimentIntensityAnalyzer()

# ---------------------------------------------------------------------------
# Financial keywords for context-aware scoring
# ---------------------------------------------------------------------------
BULLISH_KEYWORDS = [
    "rally", "surge", "gains", "bullish", "outperform", "upgrade",
    "growth", "profit", "beat", "record", "strong", "positive",
    "recovery", "rebound", "breakout", "buy", "accumulate",
    "nifty high", "sensex high", "fii buying", "dii buying",
]

BEARISH_KEYWORDS = [
    "crash", "fall", "decline", "bearish", "underperform", "downgrade",
    "loss", "miss", "weak", "negative", "selloff", "correction",
    "recession", "inflation", "rate hike", "fii selling", "outflow",
    "nifty low", "sensex low", "default", "bankruptcy", "fraud",
]

RISK_KEYWORDS = [
    "war", "conflict", "crisis", "pandemic", "lockdown", "sanction",
    "ban", "investigation", "scam", "collapse", "default", "bubble",
]

# Sector keywords for asset-specific sentiment
SECTOR_KEYWORDS = {
    "banking":    ["bank", "nbfc", "rbi", "interest rate", "npa", "credit"],
    "it":         ["it sector", "infosys", "tcs", "wipro", "tech", "software", "dollar"],
    "pharma":     ["pharma", "drug", "fda", "healthcare", "hospital"],
    "auto":       ["auto", "ev", "electric vehicle", "car", "two wheeler"],
    "energy":     ["oil", "gas", "crude", "energy", "power", "solar"],
    "fmcg":       ["fmcg", "consumer", "rural demand", "inflation"],
    "realty":     ["real estate", "realty", "housing", "property"],
    "metals":     ["steel", "metal", "aluminium", "copper", "mining"],
}


# ---------------------------------------------------------------------------
# Text Preprocessor
# ---------------------------------------------------------------------------
def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Keyword-Based Sentiment Booster
# ---------------------------------------------------------------------------
def keyword_sentiment_boost(text: str) -> float:
    text_lower = text.lower()
    boost      = 0.0

    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    risk_count    = sum(1 for kw in RISK_KEYWORDS    if kw in text_lower)

    boost += bullish_count * 0.05
    boost -= bearish_count * 0.05
    boost -= risk_count    * 0.10

    return max(-1.0, min(1.0, boost))


# ---------------------------------------------------------------------------
# Sector Detector
# ---------------------------------------------------------------------------
def detect_sectors(text: str) -> List[str]:
    text_lower = text.lower()
    detected   = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(sector)
    return detected if detected else ["general"]


# ---------------------------------------------------------------------------
# Risk Level Classifier
# ---------------------------------------------------------------------------
def classify_risk_level(
    compound_score: float,
    has_risk_keywords: bool,
) -> Dict:
    if compound_score <= -0.5 or has_risk_keywords:
        return {
            "level": "High",
            "color": "red",
            "action": "Review portfolio exposure immediately",
        }
    elif compound_score <= -0.2:
        return {
            "level": "Elevated",
            "color": "orange",
            "action": "Monitor portfolio closely",
        }
    elif compound_score >= 0.3:
        return {
            "level": "Low",
            "color": "green",
            "action": "Market sentiment positive — maintain allocation",
        }
    else:
        return {
            "level": "Neutral",
            "color": "gray",
            "action": "No immediate action required",
        }


# ---------------------------------------------------------------------------
# Core Sentiment Analyzer
# ---------------------------------------------------------------------------
def analyze_sentiment(text: str) -> Dict:
    cleaned       = preprocess_text(text)
    vader_scores  = vader.polarity_scores(cleaned)
    keyword_boost = keyword_sentiment_boost(text)

    # Combined score
    combined_score = vader_scores["compound"] + keyword_boost
    combined_score = max(-1.0, min(1.0, combined_score))

    # Sentiment label
    if combined_score >= 0.2:
        sentiment = "Positive"
        emoji     = "📈"
    elif combined_score <= -0.2:
        sentiment = "Negative"
        emoji     = "📉"
    else:
        sentiment = "Neutral"
        emoji     = "➡️"

    has_risk = any(kw in text.lower() for kw in RISK_KEYWORDS)
    sectors  = detect_sectors(text)
    risk     = classify_risk_level(combined_score, has_risk)

    return {
        "text":            text[:200] + "..." if len(text) > 200 else text,
        "sentiment":       sentiment,
        "emoji":           emoji,
        "compound_score":  round(combined_score, 4),
        "vader_scores": {
            "positive": round(vader_scores["pos"], 4),
            "negative": round(vader_scores["neg"], 4),
            "neutral":  round(vader_scores["neu"], 4),
        },
        "sectors_detected": sectors,
        "risk_level":       risk,
        "has_risk_keywords": has_risk,
    }


# ---------------------------------------------------------------------------
# Batch News Analyzer
# ---------------------------------------------------------------------------
def analyze_news_batch(articles: List[Dict]) -> Dict:
    results         = []
    sector_scores   = {}
    total_score     = 0.0

    for article in articles:
        text   = f"{article.get('title', '')} {article.get('description', '')}"
        result = analyze_sentiment(text)
        result["source"]      = article.get("source", "Unknown")
        result["published_at"] = article.get("published_at", "")
        results.append(result)

        total_score += result["compound_score"]

        for sector in result["sectors_detected"]:
            if sector not in sector_scores:
                sector_scores[sector] = []
            sector_scores[sector].append(result["compound_score"])

    # Overall market sentiment
    avg_score = total_score / len(results) if results else 0

    if avg_score >= 0.2:
        market_sentiment = "Bullish"
        market_emoji     = "🟢"
    elif avg_score <= -0.2:
        market_sentiment = "Bearish"
        market_emoji     = "🔴"
    else:
        market_sentiment = "Neutral"
        market_emoji     = "🟡"

    # Sector-wise sentiment
    sector_summary = {
        sector: {
            "avg_score":  round(np.mean(scores) if scores else 0, 4),
            "sentiment":  "Positive" if (sum(scores)/len(scores) if scores else 0) > 0.1
                          else "Negative" if (sum(scores)/len(scores) if scores else 0) < -0.1
                          else "Neutral",
            "articles":   len(scores),
        }
        for sector, scores in sector_scores.items()
    }

    return {
        "total_articles":    len(results),
        "overall_score":     round(avg_score, 4),
        "market_sentiment":  market_sentiment,
        "market_emoji":      market_emoji,
        "sector_sentiment":  sector_summary,
        "articles":          results,
        "risk_level":        classify_risk_level(avg_score, False),
    }


# ---------------------------------------------------------------------------
# Add numpy import at top
# ---------------------------------------------------------------------------
import numpy as np