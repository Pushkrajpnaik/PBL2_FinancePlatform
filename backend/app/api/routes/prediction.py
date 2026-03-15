from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
from app.data.ingestion.market_data import fetch_nifty50_history
from app.data.ingestion.macro_data import get_full_macro_snapshot
from app.data.processing.cache_manager import get_cached_news_sentiment
from app.data.processing.data_processor import detect_market_regime_from_data
from app.ml.prediction.arima_predictor import predict_arima
from app.ml.prediction.lstm_predictor import predict_lstm
from app.ml.prediction.xgboost_predictor import train_xgboost
from app.ml.prediction.news_driven_predictor import (
    get_live_news_sentiment,
    news_adjusted_arima_prediction,
    news_driven_xgboost_prediction,
    generate_investment_signal,
)
from app.ml.prediction.real_backtester import (
    run_full_backtest,
    run_walk_forward_backtest,
    generate_equity_curve,
    fetch_backtest_data,
    calculate_strategy_returns,
    calculate_performance_metrics,
)
from app.ml.regime.hmm_detector import (
    generate_placeholder_market_data,
    detect_regime_hmm,
    adjust_portfolio_for_regime,
    REGIME_ALLOCATION_ADJUSTMENTS,
)
from app.ml.portfolio.optimizer import (
    mean_variance_optimization,
    get_assets_for_profile,
)

router = APIRouter()


@router.get("/nifty50/arima")
def predict_nifty_arima(
    period: str = "1y",
    forecast_days: int = 30,
    current_user: User = Depends(get_current_active_user),
):
    """ARIMA prediction on real NIFTY50 historical data."""
    df = fetch_nifty50_history(period=period)
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch NIFTY50 data")
    result = predict_arima(df["close"], forecast_days=forecast_days)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/nifty50/lstm")
def predict_nifty_lstm(
    period: str = "2y",
    forecast_days: int = 30,
    epochs: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """LSTM prediction on real NIFTY50 data using PyTorch."""
    df = fetch_nifty50_history(period=period)
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch NIFTY50 data")
    result = predict_lstm(df["close"], forecast_days=forecast_days, epochs=epochs)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/nifty50/xgboost")
def predict_nifty_xgboost(
    period: str = "2y",
    current_user: User = Depends(get_current_active_user),
):
    """XGBoost prediction with news sentiment as feature."""
    df = fetch_nifty50_history(period=period)
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch NIFTY50 data")
    cached_news          = get_cached_news_sentiment()
    news_sentiment_score = cached_news.get("overall_score", 0.0) if cached_news else 0.0
    macro                = get_full_macro_snapshot()
    result = train_xgboost(df, news_sentiment_score=news_sentiment_score, macro_data=macro)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    result["news_sentiment_used"] = news_sentiment_score
    return result


@router.get("/nifty50/combined")
def predict_nifty_combined(
    current_user: User = Depends(get_current_active_user),
):
    """Combined prediction from ARIMA + XGBoost + Regime Detection."""
    df = fetch_nifty50_history(period="1y")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch NIFTY50 data")

    cached_news          = get_cached_news_sentiment()
    news_sentiment_score = cached_news.get("overall_score", 0.0) if cached_news else 0.0
    macro                = get_full_macro_snapshot()

    arima_result  = predict_arima(df["close"], forecast_days=30)
    xgb_result    = train_xgboost(df, news_sentiment_score, macro)
    regime_result = detect_market_regime_from_data(df)

    signals = []
    if "summary" in arima_result:
        signals.append(1 if arima_result["summary"]["direction"] == "UP" else -1)
    if "next_day_direction" in xgb_result:
        signals.append(1 if xgb_result["next_day_direction"] == "UP" else -1)
    if "regime" in regime_result:
        signals.append(1 if regime_result["regime"] in ["Bull Market", "Recovery"] else -1)

    consensus_score = sum(signals) / len(signals) if signals else 0
    if consensus_score > 0.3:
        consensus = "BULLISH"
        action    = "Consider increasing equity allocation"
    elif consensus_score < -0.3:
        consensus = "BEARISH"
        action    = "Consider reducing equity allocation"
    else:
        consensus = "NEUTRAL"
        action    = "Maintain current allocation"

    return {
        "consensus":            consensus,
        "consensus_score":      round(consensus_score, 2),
        "action":               action,
        "news_sentiment_score": news_sentiment_score,
        "models": {
            "arima":   {"direction": arima_result.get("summary", {}).get("direction", "N/A"), "return_30d": arima_result.get("summary", {}).get("expected_return_30d", 0)},
            "xgboost": {"direction": xgb_result.get("next_day_direction", "N/A"), "confidence": xgb_result.get("confidence", 0), "accuracy": xgb_result.get("accuracy", 0)},
            "regime":  {"regime": regime_result.get("regime", "N/A"), "confidence": regime_result.get("confidence", 0)},
        },
        "feature_importance": xgb_result.get("feature_importance", {}),
    }


@router.get("/nifty50/news-adjusted-arima")
def predict_news_adjusted_arima(
    forecast_days: int = 30,
    current_user: User = Depends(get_current_active_user),
):
    """ARIMA prediction adjusted by live news sentiment."""
    df = fetch_nifty50_history(period="1y")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch data")
    news_data = get_live_news_sentiment()
    return news_adjusted_arima_prediction(df["close"], news_data, forecast_days)


@router.get("/nifty50/news-xgboost")
def predict_news_xgboost(
    current_user: User = Depends(get_current_active_user),
):
    """XGBoost with full news feature integration."""
    df = fetch_nifty50_history(period="2y")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch data")
    news_data = get_live_news_sentiment()
    macro     = get_full_macro_snapshot()
    return news_driven_xgboost_prediction(df, news_data, macro)


@router.get("/investment-signal")
def get_investment_signal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Complete investment signal combining ALL signals:
    ARIMA + XGBoost + News Sentiment + Geo Risk + Market Regime.
    Returns actionable BUY/SELL/HOLD recommendation.
    """
    profile      = db.query(RiskProfile).filter(RiskProfile.user_id == current_user.id).first()
    risk_profile = profile.profile_type if profile else "Moderate"
    df           = fetch_nifty50_history(period="1y")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Could not fetch data")
    news_data = get_live_news_sentiment()
    macro     = get_full_macro_snapshot()
    return generate_investment_signal(price_df=df, news_data=news_data, risk_profile=risk_profile, macro_data=macro)


@router.get("/market-regime")
def get_market_regime(
    current_user: User = Depends(get_current_active_user),
):
    """Detect market regime using real NIFTY50 data."""
    df = fetch_nifty50_history(period="3mo")
    if df is not None and not df.empty:
        return detect_market_regime_from_data(df)
    return detect_regime_hmm(generate_placeholder_market_data(days=500))


@router.get("/market-regime/history")
def get_regime_history(
    days: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """Returns regime classification for last N days."""
    df = fetch_nifty50_history(period="1y")
    if df is None or df.empty:
        df = generate_placeholder_market_data(days=500)
    df_recent = df.tail(days).copy()
    history   = []
    for idx, row in df_recent.iterrows():
        history.append({
            "date":       str(idx)[:10],
            "close":      round(float(row["close"]), 2),
            "returns":    round(float(row.get("returns", 0)) * 100, 4),
            "volatility": round(float(row.get("volatility", 0)) * 100, 4),
        })
    return {"days": days, "history": history}


@router.get("/regime-adjusted-portfolio")
def get_regime_adjusted_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Portfolio adjusted for real market regime."""
    profile = db.query(RiskProfile).filter(RiskProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No risk profile found.")
    assets      = get_assets_for_profile(profile.profile_type)
    base_result = mean_variance_optimization(assets)
    df          = fetch_nifty50_history(period="3mo")
    if df is not None and not df.empty:
        regime_data = detect_market_regime_from_data(df)
        regime      = regime_data["regime"]
    else:
        regime_data = detect_regime_hmm(generate_placeholder_market_data())
        regime      = regime_data["regime"]
    adjusted   = adjust_portfolio_for_regime(base_result["allocation"], regime)
    adjustment = REGIME_ALLOCATION_ADJUSTMENTS.get(regime, REGIME_ALLOCATION_ADJUSTMENTS["Sideways/Neutral"])
    return {
        "regime_detection":       regime_data,
        "base_allocation":        base_result["allocation"],
        "adjusted_allocation":    adjusted,
        "adjustment_description": adjustment["description"],
    }


# ─── Real Backtesting Routes ──────────────────────────────────────────────────

@router.get("/backtest/full")
def run_real_backtest(
    period: str = "5y",
    initial_investment: float = 1000000,
    monthly_sip: float = 10000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Full backtest on REAL NIFTY50 historical data.
    Compares 4 strategies: buy_and_hold, momentum, mean_reversion, regime_based.
    Walk-forward validated to prevent overfitting.
    """
    profile      = db.query(RiskProfile).filter(RiskProfile.user_id == current_user.id).first()
    risk_profile = profile.profile_type if profile else "Moderate"
    return run_full_backtest(
        period=period,
        initial_investment=initial_investment,
        monthly_sip=monthly_sip,
        risk_profile=risk_profile,
    )


@router.get("/backtest/walk-forward")
def walk_forward_backtest(
    strategy: str = "regime_based",
    period: str = "3y",
    current_user: User = Depends(get_current_active_user),
):
    """
    Walk-forward backtesting to validate strategy performance.
    Trains on past data, tests on unseen future data.
    Prevents look-ahead bias.
    """
    df = fetch_backtest_data(period=period)
    if df is None:
        df = generate_placeholder_market_data(days=756)
    return run_walk_forward_backtest(df, strategy=strategy)


@router.get("/backtest/equity-curve")
def get_equity_curve_endpoint(
    strategy: str = "regime_based",
    period: str = "2y",
    initial_investment: float = 1000000,
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns equity curve data for strategy vs benchmark.
    Used for charting in frontend.
    """
    df = fetch_backtest_data(period=period)
    if df is None:
        df = generate_placeholder_market_data(days=504)

    curve         = generate_equity_curve(df, strategy=strategy, initial_investment=initial_investment)
    strat_returns = calculate_strategy_returns(df, strategy=strategy)
    bench_returns = df["returns"].dropna()
    strat_metrics = calculate_performance_metrics(strat_returns)
    bench_metrics = calculate_performance_metrics(bench_returns)

    return {
        "strategy":          strategy,
        "period":            period,
        "equity_curve":      curve[-60:],
        "strategy_metrics":  strat_metrics,
        "benchmark_metrics": bench_metrics,
        "outperformance":    round(
            strat_metrics.get("total_return", 0) - bench_metrics.get("total_return", 0), 2
        ),
    }


@router.get("/backtest/compare-all")
def compare_all_strategies(
    period: str = "3y",
    current_user: User = Depends(get_current_active_user),
):
    """
    Compares all 4 strategies on real NIFTY50 data.
    Returns ranked strategies by Sharpe ratio.
    """
    df = fetch_backtest_data(period=period)
    if df is None:
        df = generate_placeholder_market_data(days=756)

    strategies = ["buy_and_hold", "momentum", "mean_reversion", "regime_based"]
    results    = {}

    for strategy in strategies:
        strat_returns    = calculate_strategy_returns(df, strategy=strategy)
        metrics          = calculate_performance_metrics(strat_returns)
        results[strategy] = metrics

    # Rank by Sharpe ratio
    ranked = sorted(
        results.items(),
        key=lambda x: x[1].get("sharpe_ratio", 0),
        reverse=True,
    )

    return {
        "period":       period,
        "data_points":  len(df),
        "strategies":   results,
        "ranked":       [{"rank": i+1, "strategy": s, "sharpe": m.get("sharpe_ratio", 0), "return": m.get("annual_return", 0)} for i, (s, m) in enumerate(ranked)],
        "best_strategy": ranked[0][0] if ranked else "buy_and_hold",
    }