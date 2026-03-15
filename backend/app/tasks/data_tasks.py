from app.core.celery_app import celery_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.data_tasks.fetch_mutual_fund_nav")
def fetch_mutual_fund_nav():
    """
    Daily task — fetches latest mutual fund NAV from AMFI.
    Stores in database and updates Redis cache.
    """
    logger.info("Fetching mutual fund NAV data from AMFI...")
    try:
        from app.data.ingestion.mutual_funds import fetch_all_nav
        from app.data.processing.cache_manager import set_cache

        df = fetch_all_nav()
        if df is None or df.empty:
            return {"status": "failed", "error": "No data from AMFI"}

        # Cache latest NAV data
        nav_records = df.head(100).to_dict(orient="records")
        set_cache("nav:latest", nav_records, ttl=86400)

        logger.info(f"Fetched and cached {len(df)} NAV records")
        return {
            "status":          "success",
            "records_fetched": len(df),
            "date":            datetime.today().strftime("%Y-%m-%d"),
        }
    except Exception as e:
        logger.error(f"NAV fetch failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_stock_prices")
def fetch_stock_prices():
    """
    Fetches latest stock prices from Yahoo Finance.
    Updates Redis cache with fresh prices.
    """
    logger.info("Fetching live stock prices...")
    try:
        from app.data.ingestion.market_data import (
            fetch_current_price, INDIAN_STOCKS
        )
        from app.data.processing.cache_manager import cache_stock_price

        results = {}
        for name, symbol in INDIAN_STOCKS.items():
            price = fetch_current_price(symbol)
            if price:
                cache_stock_price(name, price)
                results[name] = price["current_price"]

        return {
            "status":          "success",
            "stocks_updated":  len(results),
            "timestamp":       datetime.now().isoformat(),
            "prices":          results,
        }
    except Exception as e:
        logger.error(f"Stock price fetch failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_market_summary")
def fetch_market_summary():
    """
    Fetches and caches market summary every 5 minutes.
    """
    logger.info("Fetching market summary...")
    try:
        from app.data.ingestion.market_data import get_market_summary
        from app.data.processing.cache_manager import cache_market_summary

        summary = get_market_summary()
        cache_market_summary(summary)

        logger.info("Market summary cached successfully")
        return {
            "status":    "success",
            "timestamp": datetime.now().isoformat(),
            "data":      summary,
        }
    except Exception as e:
        logger.error(f"Market summary fetch failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_and_analyze_news")
def fetch_and_analyze_news():
    """
    Hourly task — fetches live news from RSS feeds
    and runs sentiment analysis.
    Stores results in cache and generates portfolio signals.
    """
    logger.info("Fetching and analyzing live news...")
    try:
        from app.data.ingestion.news_fetcher import fetch_all_news
        from app.ml.nlp.sentiment import analyze_news_batch
        from app.data.processing.cache_manager import cache_news_sentiment
        from app.data.processing.data_processor import process_news_for_portfolio_signal

        # Fetch live news
        articles = fetch_all_news(max_per_feed=10)
        if not articles:
            return {"status": "failed", "error": "No articles fetched"}

        # Run sentiment analysis
        sentiment_result = analyze_news_batch(articles)

        # Generate portfolio signal
        portfolio_signal = process_news_for_portfolio_signal(
            sentiment_result,
            current_regime="Bull Market",
        )

        # Cache results
        full_result = {
            **sentiment_result,
            "portfolio_signal": portfolio_signal,
            "cached_at":        datetime.now().isoformat(),
        }
        cache_news_sentiment(full_result)

        logger.info(f"Analyzed {len(articles)} articles. Signal: {portfolio_signal['news_signal']}")
        return {
            "status":            "success",
            "articles_analyzed": len(articles),
            "market_sentiment":  sentiment_result["market_sentiment"],
            "portfolio_signal":  portfolio_signal["news_signal"],
            "timestamp":         datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"News analysis failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.fetch_macro_data")
def fetch_macro_data():
    """
    Weekly task — fetches macroeconomic data.
    """
    logger.info("Fetching macro data...")
    try:
        from app.data.ingestion.macro_data import get_full_macro_snapshot
        from app.data.processing.cache_manager import set_cache

        macro = get_full_macro_snapshot()
        set_cache("macro:snapshot", macro, ttl=86400)

        return {"status": "success", "data": macro}
    except Exception as e:
        logger.error(f"Macro data fetch failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.data_tasks.update_nifty_history")
def update_nifty_history():
    """
    Daily task — fetches and caches NIFTY50 historical data.
    """
    logger.info("Updating NIFTY50 history...")
    try:
        from app.data.ingestion.market_data import fetch_nifty50_history
        from app.data.processing.cache_manager import cache_nifty_history
        from app.data.processing.data_processor import (
            calculate_technical_indicators,
            detect_market_regime_from_data,
        )

        df = fetch_nifty50_history(period="1y")
        if df is None or df.empty:
            return {"status": "failed", "error": "No NIFTY data"}

        # Add technical indicators
        df = calculate_technical_indicators(df)

        # Detect regime from real data
        regime = detect_market_regime_from_data(df)

        # Cache results
        history = df.tail(30).reset_index()
        history["date"] = history.iloc[:, 0].astype(str).str[:10]
        history_records = history[["date", "close", "returns", "rsi", "macd"]].to_dict(orient="records")

        cache_nifty_history("1y", {
            "history": history_records,
            "regime":  regime,
        })

        logger.info(f"NIFTY history updated. Regime: {regime['regime']}")
        return {
            "status":      "success",
            "data_points": len(df),
            "regime":      regime["regime"],
        }
    except Exception as e:
        logger.error(f"NIFTY history update failed: {e}")
        return {"status": "failed", "error": str(e)}