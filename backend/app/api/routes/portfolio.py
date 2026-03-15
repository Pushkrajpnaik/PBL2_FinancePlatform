from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
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
from app.ml.prediction.shap_explainer import (
    explain_portfolio_recommendation,
    run_strategy_backtest,
)

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResult)
def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
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
        raise HTTPException(status_code=400, detail="Invalid method.")
    result["investment_amount"] = request.investment_amount
    result["allocated_amounts"] = {
        asset: round(request.investment_amount * pct / 100, 2)
        for asset, pct in result["allocation"].items()
    }
    return result


@router.post("/optimize/all", response_model=AllMethodsResult)
def optimize_all_methods(
    request: PortfolioOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
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
    all_results = {"markowitz": markowitz, "risk_parity": rp, "cvar": cvar, "black_litterman": bl}
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


@router.get("/my-portfolio")
def get_my_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No risk profile found.")
    assets = get_assets_for_profile(profile.profile_type)
    result = mean_variance_optimization(assets)
    return {
        "user_id":      current_user.id,
        "risk_profile": profile.profile_type,
        "risk_score":   profile.score,
        "portfolio":    result,
    }


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