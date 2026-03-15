import httpx
from typing import List, Dict
from datetime import datetime

# ---------------------------------------------------------------------------
# Placeholder news data
# Replace with real RSS feeds in production:
# - Economic Times RSS
# - Moneycontrol RSS
# - Reuters India RSS
# ---------------------------------------------------------------------------
PLACEHOLDER_NEWS = [
    {
        "title": "Nifty50 hits new all-time high as FII buying surges in banking stocks",
        "description": "Foreign institutional investors bought equities worth Rs 4,500 crore as market rallied strongly.",
        "source": "Economic Times",
        "published_at": "2024-01-15T09:30:00",
        "category": "market",
    },
    {
        "title": "RBI holds repo rate steady at 6.5% in latest monetary policy meeting",
        "description": "Reserve Bank of India keeps interest rates unchanged citing stable inflation outlook.",
        "source": "Moneycontrol",
        "published_at": "2024-01-15T10:00:00",
        "category": "economy",
    },
    {
        "title": "IT sector faces headwinds as US recession fears impact deal flows",
        "description": "Major IT companies report slowdown in new deal signings amid global uncertainty.",
        "source": "Business Standard",
        "published_at": "2024-01-15T11:00:00",
        "category": "sector",
    },
    {
        "title": "Inflation rises to 5.8% driven by food prices surge across India",
        "description": "CPI inflation inches higher as vegetable and cereal prices remain elevated.",
        "source": "Reuters India",
        "published_at": "2024-01-15T12:00:00",
        "category": "economy",
    },
    {
        "title": "Auto sector reports record monthly sales driven by festive demand",
        "description": "Passenger vehicle sales hit record high as consumer sentiment improves significantly.",
        "source": "Economic Times",
        "published_at": "2024-01-15T13:00:00",
        "category": "sector",
    },
    {
        "title": "Pharma stocks rally after USFDA approves key drug applications",
        "description": "Indian pharmaceutical companies gain on positive regulatory developments from US market.",
        "source": "Moneycontrol",
        "published_at": "2024-01-15T14:00:00",
        "category": "sector",
    },
    {
        "title": "Crude oil prices surge 3% on geopolitical tensions in Middle East",
        "description": "Global crude oil prices rise sharply raising concerns about India's trade deficit.",
        "source": "Business Standard",
        "published_at": "2024-01-15T15:00:00",
        "category": "global",
    },
    {
        "title": "Mid-cap and small-cap funds see strong SIP inflows in December",
        "description": "Mutual fund industry reports record SIP collections as retail investors stay committed.",
        "source": "Economic Times",
        "published_at": "2024-01-15T16:00:00",
        "category": "mutual_funds",
    },
]


async def fetch_live_news(category: str = "all") -> List[Dict]:
    """
    Fetches live financial news.
    Currently returns placeholder data.
    Replace with real RSS/API calls in production.
    """
    if category == "all":
        return PLACEHOLDER_NEWS
    return [n for n in PLACEHOLDER_NEWS if n["category"] == category]


async def fetch_news_for_asset(asset: str) -> List[Dict]:
    """
    Fetches news specific to an asset or sector.
    """
    asset_keywords = {
        "equity":       ["nifty", "sensex", "stock", "share"],
        "debt":         ["rbi", "interest rate", "bond", "yield"],
        "gold":         ["gold", "commodity", "mcx"],
        "banking":      ["bank", "nbfc", "rbi"],
        "it":           ["it sector", "tech", "software"],
        "pharma":       ["pharma", "drug", "healthcare"],
    }

    keywords = asset_keywords.get(asset.lower(), [asset.lower()])
    filtered = [
        n for n in PLACEHOLDER_NEWS
        if any(kw in n["title"].lower() or kw in n["description"].lower()
               for kw in keywords)
    ]
    return filtered if filtered else PLACEHOLDER_NEWS[:3]