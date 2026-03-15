from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.data.ingestion.market_data import (
    fetch_current_price,
    fetch_nifty50_history,
    get_market_summary,
    calculate_returns_stats,
    INDIAN_STOCKS,
    INDIAN_INDICES,
    COMMODITY_SYMBOLS,
)
from app.data.ingestion.mutual_funds import (
    fetch_nav_for_scheme,
    get_popular_funds_data,
    search_fund_by_name,
)
from app.data.ingestion.macro_data import (
    get_full_macro_snapshot,
    fetch_gold_price,
)
from app.data.ingestion.news_fetcher import (
    fetch_all_news,
    fetch_news_for_keyword,
    get_news_categories,
)
from app.ml.nlp.sentiment import analyze_news_batch
from app.data.processing.cache_manager import (
    get_cached_market_summary,
    cache_market_summary,
    get_cached_nifty_history,
    cache_nifty_history,
    get_cached_news_sentiment,
    cache_news_sentiment,
)
from app.data.processing.data_processor import (
    calculate_technical_indicators,
    detect_market_regime_from_data,
    process_news_for_portfolio_signal,
)

router = APIRouter()


@router.get("/summary")
def get_market_summary_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """Live market summary with Redis caching — NIFTY, SENSEX, Gold, USD/INR, Crude."""
    # Try cache first
    cached = get_cached_market_summary()
    if cached:
        cached["from_cache"] = True
        return cached

    # Fetch fresh data
    data = get_market_summary()
    cache_market_summary(data)
    data["from_cache"] = False
    return data


@router.get("/nifty50")
def get_nifty50(
    period: str = "1y",
    current_user: User = Depends(get_current_active_user)
):
    """NIFTY50 historical data with returns stats and technical indicators."""
    # Try cache first
    cached = get_cached_nifty_history(period)
    if cached:
        cached["from_cache"] = True
        return cached

    df = fetch_nifty50_history(period=period)
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch NIFTY50 data")

    # Add technical indicators
    df    = calculate_technical_indicators(df)
    stats = calculate_returns_stats(df)

    # Detect regime from real data
    regime = detect_market_regime_from_data(df)

    # Reset index and handle column names
    df_reset         = df.reset_index()
    date_col         = df_reset.columns[0]
    df_reset         = df_reset.rename(columns={date_col: "date"})
    df_reset["date"] = df_reset["date"].astype(str).str[:10]

    available_cols = ["date", "close", "returns", "volatility", "rsi", "macd", "sma_20", "sma_50"]
    cols           = [c for c in available_cols if c in df_reset.columns]
    history        = df_reset.tail(30)[cols].to_dict(orient="records")

    result = {
        "symbol":     "NIFTY50",
        "period":     period,
        "stats":      stats,
        "regime":     regime,
        "history":    history,
        "from_cache": False,
    }

    cache_nifty_history(period, result)
    return result


@router.get("/stock/{symbol}")
def get_stock_price(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    """Live stock price for NSE listed stock."""
    yahoo_symbol = INDIAN_STOCKS.get(symbol.upper(), f"{symbol}.NS")
    price        = fetch_current_price(yahoo_symbol)
    if not price:
        raise HTTPException(status_code=404, detail=f"Could not fetch price for {symbol}")
    price["symbol"] = symbol
    return price


@router.get("/stocks/all")
def get_all_stocks(
    current_user: User = Depends(get_current_active_user)
):
    """Live prices for all tracked Indian stocks."""
    results = {}
    for name, symbol in INDIAN_STOCKS.items():
        price = fetch_current_price(symbol)
        if price:
            results[name] = price
    return {"stocks": results, "count": len(results)}


@router.get("/mutual-funds/popular")
def get_popular_funds(
    current_user: User = Depends(get_current_active_user)
):
    """NAV and returns for popular mutual funds."""
    funds = get_popular_funds_data()
    return {"funds": funds, "count": len(funds)}


@router.get("/mutual-funds/search")
def search_funds(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """Search mutual funds by name."""
    results = search_fund_by_name(query)
    return {"results": results, "query": query}


@router.get("/mutual-funds/{scheme_code}")
def get_fund_details(
    scheme_code: str,
    current_user: User = Depends(get_current_active_user)
):
    """Detailed NAV history and stats for a specific fund."""
    data = fetch_nav_for_scheme(scheme_code)
    if not data:
        raise HTTPException(status_code=404, detail="Fund not found")
    return data


@router.get("/macro")
def get_macro_data(
    current_user: User = Depends(get_current_active_user)
):
    """Full macro snapshot — forex, commodities, rates."""
    return get_full_macro_snapshot()


@router.get("/gold")
def get_gold_price(
    current_user: User = Depends(get_current_active_user)
):
    """Current gold price in USD and INR."""
    data = fetch_gold_price()
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch gold price")
    return data


@router.get("/news/live")
async def get_live_news(
    category: str = "all",
    with_sentiment: bool = True,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetches LIVE news from RSS feeds with Redis caching.
    Refreshes every hour automatically.
    Add force_refresh=true to bypass cache.
    """
    # Try cache first
    if not force_refresh:
        cached = get_cached_news_sentiment()
        if cached:
            cached["from_cache"] = True
            return cached

    articles = fetch_all_news(max_per_feed=8)
    if not articles:
        raise HTTPException(status_code=503, detail="Could not fetch live news")

    if category != "all":
        categorized = get_news_categories(articles)
        articles    = categorized.get(category, articles)

    if with_sentiment:
        result           = analyze_news_batch(articles)
        portfolio_signal = process_news_for_portfolio_signal(
            result, "Bull Market"
        )
        result["portfolio_signal"] = portfolio_signal
        result["from_cache"]       = False

        # Cache for 1 hour
        cache_news_sentiment(result)
        return result

    return {
        "source":   "live_rss",
        "articles": articles,
        "total":    len(articles),
    }


@router.get("/news/live/sector/{sector}")
async def get_live_sector_news(
    sector: str,
    current_user: User = Depends(get_current_active_user)
):
    """Live news filtered by sector with sentiment."""
    articles = fetch_news_for_keyword(sector)
    result   = analyze_news_batch(articles) if articles else {}
    return {
        "sector":    sector,
        "articles":  articles,
        "sentiment": result.get("market_sentiment", "Neutral"),
        "score":     result.get("overall_score", 0),
    }


@router.get("/portfolio-signal")
async def get_portfolio_signal(
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns combined portfolio adjustment signal
    from live news sentiment + real market regime.
    This is the news → portfolio pipeline!
    """
    # Get live news sentiment from cache or fetch fresh
    cached_news = get_cached_news_sentiment()
    if not cached_news:
        articles    = fetch_all_news(max_per_feed=5)
        cached_news = analyze_news_batch(articles) if articles else {}
        if cached_news:
            cache_news_sentiment(cached_news)

    # Get real market regime from NIFTY data
    df = fetch_nifty50_history(period="3mo")
    if df is not None and not df.empty:
        regime_data = detect_market_regime_from_data(df)
        regime      = regime_data["regime"]
        regime_conf = regime_data["confidence"]
    else:
        regime      = "Sideways/Neutral"
        regime_conf = 60.0

    # Generate combined portfolio signal
    signal = process_news_for_portfolio_signal(cached_news, regime)

    return {
        "signal":           signal,
        "market_regime":    regime,
        "regime_confidence": regime_conf,
        "news_sentiment":   cached_news.get("market_sentiment", "Neutral"),
        "news_score":       cached_news.get("overall_score", 0),
        "top_risk_sectors": [
            sector for sector, data in cached_news.get("sector_sentiment", {}).items()
            if isinstance(data, dict) and data.get("avg_score", 0) < -0.2
        ],
        "top_opportunity_sectors": [
            sector for sector, data in cached_news.get("sector_sentiment", {}).items()
            if isinstance(data, dict) and data.get("avg_score", 0) > 0.2
        ],
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/regime/real")
def get_real_market_regime(
    period: str = "3mo",
    current_user: User = Depends(get_current_active_user)
):
    """
    Detects current market regime from REAL NIFTY50 price data.
    Uses rule-based detection on actual historical prices.
    """
    df = fetch_nifty50_history(period=period)
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch market data")

    regime = detect_market_regime_from_data(df)
    return regime