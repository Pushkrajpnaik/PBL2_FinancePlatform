from app.core.celery_app import celery_app
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.data_tasks.fetch_mutual_fund_nav")
def fetch_mutual_fund_nav():
    """
    Daily task — fetches latest mutual fund NAV from AMFI.
    Placeholder: replace URL with real AMFI API endpoint.
    """
    logger.info("Fetching mutual fund NAV data...")
    try:
        # Placeholder data — replace with real AMFI API
        placeholder_nav = [
            {"scheme_code": "120503", "scheme_name": "Axis Bluechip Fund", "nav": 52.34, "date": datetime.today().strftime("%Y-%m-%d")},
            {"scheme_code": "120465", "scheme_name": "Mirae Asset Large Cap", "nav": 98.12, "date": datetime.today().strftime("%Y-%m-%d")},
            {"scheme_code": "119598", "scheme_name": "Parag Parikh Flexi Cap", "nav": 71.45, "date": datetime.today().strftime("%Y-%m-%d")},
            {"scheme_code": "120716", "scheme_name": "SBI Small Cap Fund", "nav": 145.67, "date": datetime.today().strftime("%Y-%m-%d")},
        ]
        logger.info(f"Fetched {len(placeholder_nav)} NAV records.")
        return {
            "status":        "success",
            "records_fetched": len(placeholder_nav),
            "date":          datetime.today().strftime("%Y-%m-%d"),
            "data":          placeholder_nav,
        }
    except Exception as e:
        logger.error(f"NAV fetch failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_stock_prices")
def fetch_stock_prices():
    """
    Fetches latest stock prices from NSE/BSE.
    Placeholder: replace with real NSE API.
    """
    logger.info("Fetching stock prices...")
    placeholder_prices = [
        {"symbol": "RELIANCE", "exchange": "NSE", "close": 2456.78, "date": datetime.today().strftime("%Y-%m-%d")},
        {"symbol": "TCS",      "exchange": "NSE", "close": 3567.90, "date": datetime.today().strftime("%Y-%m-%d")},
        {"symbol": "HDFCBANK", "exchange": "NSE", "close": 1678.45, "date": datetime.today().strftime("%Y-%m-%d")},
        {"symbol": "INFY",     "exchange": "NSE", "close": 1456.23, "date": datetime.today().strftime("%Y-%m-%d")},
        {"symbol": "ICICIBANK","exchange": "NSE", "close": 987.65,  "date": datetime.today().strftime("%Y-%m-%d")},
    ]
    return {
        "status":          "success",
        "records_fetched": len(placeholder_prices),
        "data":            placeholder_prices,
    }


@celery_app.task(name="app.tasks.data_tasks.fetch_and_analyze_news")
def fetch_and_analyze_news():
    """
    Hourly task — fetches financial news and runs sentiment analysis.
    """
    logger.info("Fetching and analyzing news...")
    try:
        from app.ml.nlp.sentiment import analyze_sentiment
        news_headlines = [
            "Nifty50 surges 200 points on strong FII buying",
            "RBI keeps repo rate unchanged at 6.5%",
            "IT sector faces headwinds as US slowdown fears rise",
            "Gold prices rise on global uncertainty",
            "Auto sector reports record monthly sales",
        ]
        results = []
        for headline in news_headlines:
            sentiment = analyze_sentiment(headline)
            results.append({
                "headline":  headline,
                "sentiment": sentiment["sentiment"],
                "score":     sentiment["compound_score"],
            })
        logger.info(f"Analyzed {len(results)} news articles.")
        return {
            "status":           "success",
            "articles_analyzed": len(results),
            "results":          results,
            "timestamp":        datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"News analysis failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_macro_data")
def fetch_macro_data():
    """
    Weekly task — fetches macroeconomic data from RBI/MOSPI.
    Placeholder: replace with real RBI DBIE API.
    """
    logger.info("Fetching macro data...")
    placeholder_macro = {
        "cpi_inflation":    5.8,
        "wpi_inflation":    2.3,
        "repo_rate":        6.5,
        "gdp_growth":       7.2,
        "iip_growth":       4.1,
        "usd_inr":          83.45,
        "date":             datetime.today().strftime("%Y-%m-%d"),
    }
    return {
        "status": "success",
        "data":   placeholder_macro,
    }