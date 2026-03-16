from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
from app.ml.portfolio.ensemble_optimizer import run_ensemble_optimization
from app.schemas.portfolio import (
    PortfolioOptimizationRequest,
    OptimizationResult,
    AllMethodsResult,
)
from app.ml.portfolio.optimizer import (
    mean_variance_optimization,
    risk_parity_optimization,
    cvar_optimization,
    black_litterman_optimization,
    get_assets_for_profile,
)
from app.ml.portfolio.dynamic_optimizer import get_dynamic_portfolio
from app.ml.prediction.shap_explainer import (
    explain_portfolio_recommendation,
    run_strategy_backtest,
)
from app.data.processing.cache_manager import get_cached_news_sentiment
from app.data.ingestion.market_data import fetch_nifty50_history
from app.data.processing.data_processor import (
    detect_market_regime_from_data,
    process_news_for_portfolio_signal,
)

router = APIRouter()


# ─── GET routes first (specific before generic) ───────────────────────────────

@router.get("/optimize/dynamic/auto")
def auto_dynamic_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fully automatic dynamic portfolio optimization.
    Uses user's saved risk profile + real market data + live news.
    No input needed — fully automated!
    """
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found. Please complete risk assessment first."
        )

    assets = get_assets_for_profile(profile.profile_type)

    # Get news signal
    cached_news = get_cached_news_sentiment()
    news_signal = None
    if cached_news:
        df = fetch_nifty50_history(period="3mo")
        if df is not None and not df.empty:
            regime      = detect_market_regime_from_data(df)["regime"]
            news_signal = process_news_for_portfolio_signal(cached_news, regime)

    result = get_dynamic_portfolio(
        assets=assets,
        method="markowitz",
        investment_amount=1000000,
        news_signal=news_signal,
    )

    result["user_risk_profile"] = profile.profile_type
    result["user_risk_score"]   = profile.score
    result["news_signal"]       = news_signal
    return result


@router.get("/compare/static-vs-dynamic")
def compare_static_vs_dynamic(
    risk_profile: str = "Moderate",
    investment_amount: float = 1000000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Compares static (hardcoded) vs dynamic (real data) portfolio optimization.
    Shows the difference real data makes!
    """
    assets = get_assets_for_profile(risk_profile)

    # Static optimization
    static_result = mean_variance_optimization(assets)

    # Dynamic optimization
    cached_news = get_cached_news_sentiment()
    news_signal = None
    if cached_news:
        df = fetch_nifty50_history(period="3mo")
        if df is not None and not df.empty:
            regime      = detect_market_regime_from_data(df)["regime"]
            news_signal = process_news_for_portfolio_signal(cached_news, regime)

    dynamic_result = get_dynamic_portfolio(
        assets=assets,
        method="markowitz",
        investment_amount=investment_amount,
        news_signal=news_signal,
    )

    # Compare allocations
    allocation_diff = {}
    for asset in assets:
        static_w  = static_result["allocation"].get(asset, 0)
        dynamic_w = dynamic_result["allocation"].get(asset, 0)
        allocation_diff[asset] = {
            "static":     static_w,
            "dynamic":    dynamic_w,
            "difference": round(dynamic_w - static_w, 2),
        }

    return {
        "risk_profile":      risk_profile,
        "investment_amount": investment_amount,
        "static_portfolio": {
            "method":          "Markowitz (Hardcoded Returns)",
            "expected_return": static_result["expected_return"],
            "expected_risk":   static_result["expected_risk"],
            "sharpe_ratio":    static_result["sharpe_ratio"],
            "allocation":      static_result["allocation"],
        },
        "dynamic_portfolio": {
            "method":          dynamic_result["method"],
            "expected_return": dynamic_result["expected_return"],
            "expected_risk":   dynamic_result["expected_risk"],
            "sharpe_ratio":    dynamic_result["sharpe_ratio"],
            "allocation":      dynamic_result["allocation"],
            "data_quality":    dynamic_result["data_quality"],
            "news_adjusted":   dynamic_result.get("news_adjusted", False),
        },
        "allocation_differences": allocation_diff,
        "news_signal":            news_signal,
    }


@router.get("/my-portfolio")
def get_my_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get optimized portfolio based on user's saved risk profile.
    Uses Markowitz optimization by default.
    """
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found. Please complete risk assessment first."
        )

    assets = get_assets_for_profile(profile.profile_type)
    result = mean_variance_optimization(assets)

    return {
        "user_id":      current_user.id,
        "risk_profile": profile.profile_type,
        "risk_score":   profile.score,
        "portfolio":    result,
    }

@router.get("/optimize/ensemble/auto")
def ensemble_auto_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Ensemble portfolio — combines ALL 4 optimization methods.
    Weights automatically determined by market regime + news signal.
    This is the most sophisticated optimization available.
    """
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found."
        )

    assets = get_assets_for_profile(profile.profile_type)

    # Get regime
    df = fetch_nifty50_history(period="3mo")
    if df is not None and not df.empty:
        regime = detect_market_regime_from_data(df)["regime"]
    else:
        regime = "Sideways/Neutral"

    # Get news signal
    cached_news = get_cached_news_sentiment()
    news_signal = None
    if cached_news:
        news_signal = process_news_for_portfolio_signal(cached_news, regime)

    result = run_ensemble_optimization(
        assets=assets,
        risk_profile=profile.profile_type,
        regime=regime,
        news_signal=news_signal,
        investment_amount=1000000,
    )

    result["user_risk_profile"] = profile.profile_type
    return result


@router.post("/optimize/ensemble")
def ensemble_portfolio(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Ensemble portfolio with custom inputs.
    Combines all 4 methods with regime-aware weighting.
    """
    assets = get_assets_for_profile(request.risk_profile)

    df = fetch_nifty50_history(period="3mo")
    regime = detect_market_regime_from_data(df)["regime"] if df is not None else "Sideways/Neutral"

    cached_news = get_cached_news_sentiment()
    news_signal = None
    if cached_news:
        news_signal = process_news_for_portfolio_signal(cached_news, regime)

    return run_ensemble_optimization(
        assets=assets,
        risk_profile=request.risk_profile,
        regime=regime,
        news_signal=news_signal,
        investment_amount=request.investment_amount,
        investor_views=request.investor_views,
    )

# ─── POST routes after GET routes ─────────────────────────────────────────────

@router.post("/optimize/dynamic")
def optimize_dynamic_portfolio(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Dynamic portfolio optimization using REAL historical returns
    and correlations from Yahoo Finance.
    Also incorporates live news sentiment signal.
    Novel: Real data + News signal combined!
    """
    assets = get_assets_for_profile(request.risk_profile)

    cached_news = get_cached_news_sentiment()
    news_signal = None
    if cached_news:
        df = fetch_nifty50_history(period="3mo")
        if df is not None and not df.empty:
            regime      = detect_market_regime_from_data(df)["regime"]
            news_signal = process_news_for_portfolio_signal(cached_news, regime)

    result = get_dynamic_portfolio(
        assets=assets,
        method=request.method,
        investment_amount=request.investment_amount,
        news_signal=news_signal,
    )

    return result


@router.post("/optimize/all", response_model=AllMethodsResult)
def optimize_all_methods(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run all 4 optimization algorithms and compare results.
    Returns the best method based on Sharpe ratio.
    """
    assets    = get_assets_for_profile(request.risk_profile)
    markowitz = mean_variance_optimization(assets)
    rp        = risk_parity_optimization(assets)
    cvar      = cvar_optimization(assets)
    bl        = black_litterman_optimization(assets, request.investor_views)

    for r in [markowitz, rp, cvar, bl]:
        r["investment_amount"] = request.investment_amount
        r["allocated_amounts"] = {
            asset: round(request.investment_amount * pct / 100, 2)
            for asset, pct in r["allocation"].items()
        }

    all_results = {
        "markowitz":       markowitz,
        "risk_parity":     rp,
        "cvar":            cvar,
        "black_litterman": bl,
    }
    best = max(all_results.values(), key=lambda x: x["sharpe_ratio"])

    return {
        "risk_profile":      request.risk_profile,
        "investment_amount": request.investment_amount,
        "markowitz":         markowitz,
        "risk_parity":       rp,
        "cvar":              cvar,
        "black_litterman":   bl,
        "recommended":       best,
    }


@router.post("/optimize", response_model=OptimizationResult)
def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Optimize portfolio using selected algorithm.
    Methods: markowitz / risk_parity / cvar / black_litterman
    """
    assets = get_assets_for_profile(request.risk_profile)

    if request.method == "markowitz":
        result = mean_variance_optimization(assets)
    elif request.method == "risk_parity":
        result = risk_parity_optimization(assets)
    elif request.method == "cvar":
        result = cvar_optimization(assets)
    elif request.method == "black_litterman":
        result = black_litterman_optimization(assets, request.investor_views)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid method. Choose: markowitz, risk_parity, cvar, black_litterman"
        )

    result["investment_amount"] = request.investment_amount
    result["allocated_amounts"] = {
        asset: round(request.investment_amount * pct / 100, 2)
        for asset, pct in result["allocation"].items()
    }
    return result


@router.post("/explain")
def explain_portfolio(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    SHAP-powered explanation for portfolio recommendation.
    Shows exactly WHY each asset was selected.
    """
    profile    = db.query(RiskProfile).filter(RiskProfile.user_id == current_user.id).first()
    risk_score = profile.score if profile else 50.0
    assets     = get_assets_for_profile(request.risk_profile)
    result     = mean_variance_optimization(assets)

    explanation = explain_portfolio_recommendation(
        risk_profile=request.risk_profile,
        risk_score=risk_score,
        allocation=result["allocation"],
        regime="Bull Market",
    )

    return {
        "portfolio":   result,
        "explanation": explanation,
    }


@router.post("/backtest")
def backtest_portfolio(
    request: PortfolioOptimizationRequest,
    years: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Walk-forward backtesting vs Nifty50 benchmark.
    Validates strategy performance over historical data.
    """
    return run_strategy_backtest(
        risk_profile=request.risk_profile,
        initial_investment=request.investment_amount,
        years=years,
    )