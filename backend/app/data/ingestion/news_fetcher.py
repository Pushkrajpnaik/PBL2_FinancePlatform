import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Live Indian Financial News RSS Feeds
# ---------------------------------------------------------------------------
RSS_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Economic Times Economy":  "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "Moneycontrol Markets":    "https://www.moneycontrol.com/rss/latestnews.xml",
    "Business Standard":       "https://www.business-standard.com/rss/markets-106.rss",
    "Mint Markets":            "https://www.livemint.com/rss/markets",
    "NDTV Profit":             "https://feeds.feedburner.com/ndtvprofit-latest",
}


def clean_html(text: str) -> str:
    """Removes HTML tags from text."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text).strip()


def fetch_rss_feed(feed_name: str, feed_url: str, max_items: int = 10) -> List[Dict]:
    """Fetches articles from a single RSS feed."""
    try:
        feed     = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:max_items]:
            title       = clean_html(entry.get("title", ""))
            description = clean_html(entry.get("summary", entry.get("description", "")))
            published   = entry.get("published", entry.get("updated", ""))

            if not title:
                continue

            articles.append({
                "title":        title,
                "description":  description[:300] if description else "",
                "source":       feed_name,
                "url":          entry.get("link", ""),
                "published_at": published,
                "fetched_at":   datetime.now().isoformat(),
            })

        logger.info(f"Fetched {len(articles)} articles from {feed_name}")
        return articles

    except Exception as e:
        logger.error(f"Failed to fetch {feed_name}: {e}")
        return []


def fetch_all_news(max_per_feed: int = 10) -> List[Dict]:
    """
    Fetches news from all RSS feeds.
    Returns combined list of articles.
    """
    all_articles = []

    for feed_name, feed_url in RSS_FEEDS.items():
        articles = fetch_rss_feed(feed_name, feed_url, max_per_feed)
        all_articles.extend(articles)

    # Deduplicate by title
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        title_key = article["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    logger.info(f"Total unique articles fetched: {len(unique_articles)}")
    return unique_articles


def fetch_news_for_keyword(keyword: str, max_items: int = 20) -> List[Dict]:
    """
    Filters fetched news for a specific keyword.
    """
    all_news = fetch_all_news()
    keyword_lower = keyword.lower()
    filtered = [
        article for article in all_news
        if keyword_lower in article["title"].lower()
        or keyword_lower in article["description"].lower()
    ]
    return filtered[:max_items]


def get_news_categories(articles: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categorizes articles by sector keywords.
    """
    categories = {
        "banking":   [],
        "it":        [],
        "pharma":    [],
        "auto":      [],
        "energy":    [],
        "fmcg":      [],
        "realty":    [],
        "metals":    [],
        "economy":   [],
        "general":   [],
    }

    category_keywords = {
        "banking":  ["bank", "nbfc", "rbi", "interest rate", "npa", "hdfc", "sbi", "icici"],
        "it":       ["it ", "tcs", "infosys", "wipro", "tech mahindra", "software", "it sector"],
        "pharma":   ["pharma", "drug", "fda", "cipla", "sun pharma", "healthcare"],
        "auto":     ["auto", "maruti", "tata motors", "bajaj", "hero", "electric vehicle", "ev"],
        "energy":   ["oil", "gas", "crude", "ongc", "reliance", "solar", "power"],
        "fmcg":     ["fmcg", "hindustan unilever", "nestle", "consumer", "itc"],
        "realty":   ["real estate", "realty", "dlf", "housing", "property"],
        "metals":   ["steel", "tata steel", "jsw", "metal", "aluminium", "copper"],
        "economy":  ["gdp", "inflation", "cpi", "rbi", "budget", "fiscal", "monsoon"],
    }

    for article in articles:
        text = (article["title"] + " " + article["description"]).lower()
        categorized = False
        for category, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                categories[category].append(article)
                categorized = True
                break
        if not categorized:
            categories["general"].append(article)

    return categories