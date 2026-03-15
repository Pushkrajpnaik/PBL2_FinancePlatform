from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.tasks.portfolio_tasks import check_all_portfolio_drift, rebalance_portfolio
from app.tasks.data_tasks import fetch_mutual_fund_nav, fetch_and_analyze_news, fetch_stock_prices
from app.tasks.model_tasks import retrain_all_models, run_backtesting

from app.models.risk_profile import RiskProfile
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.ml.simulation.monte_carlo import (
    run_monte_carlo,
    calculate_goal_success_probability,
    RISK_PROFILE_ASSUMPTIONS,
)

router = APIRouter()


@router.post("/run", response_model=SimulationResponse)
def run_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run Monte Carlo simulation with 10,000 scenarios.
    Returns full probability distribution, VaR, CVaR,
    and goal success probability.
    """

    if request.risk_profile not in RISK_PROFILE_ASSUMPTIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid risk profile. Choose: Conservative, Moderate, or Aggressive",
        )

    assumptions = RISK_PROFILE_ASSUMPTIONS[request.risk_profile]

    results = run_monte_carlo(
        initial_investment=request.initial_investment,
        monthly_sip=request.monthly_sip,
        expected_annual_return=assumptions["expected_annual_return"],
        annual_volatility=assumptions["annual_volatility"],
        time_horizon_years=request.time_horizon_years,
    )

    if request.target_amount:
        goal_analysis = calculate_goal_success_probability(
            initial_investment=request.initial_investment,
            monthly_sip=request.monthly_sip,
            expected_annual_return=assumptions["expected_annual_return"],
            annual_volatility=assumptions["annual_volatility"],
            time_horizon_years=request.time_horizon_years,
            target_amount=request.target_amount,
        )
        results["goal_analysis"] = goal_analysis

    return results


@router.post("/quick")
def quick_simulation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Runs a quick simulation using the user's saved risk profile.
    Uses default values: 10,000 invested, 5,000 SIP, 10 year horizon.
    """

    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found. Please complete risk assessment first.",
        )

    assumptions = RISK_PROFILE_ASSUMPTIONS[profile.profile_type]

    results = run_monte_carlo(
        initial_investment=10000,
        monthly_sip=5000,
        expected_annual_return=assumptions["expected_annual_return"],
        annual_volatility=assumptions["annual_volatility"],
        time_horizon_years=10,
    )

    results["used_profile"] = profile.profile_type
    return results


# ---------------- TASK TRIGGERS ---------------- #

@router.post("/tasks/trigger-nav-fetch")
def trigger_nav_fetch(current_user: User = Depends(get_current_active_user)):
    """Manually trigger mutual fund NAV fetch."""
    task = fetch_mutual_fund_nav.delay()
    return {"task_id": task.id, "status": "triggered", "task": "fetch_mutual_fund_nav"}


@router.post("/tasks/trigger-news-analysis")
def trigger_news_analysis(current_user: User = Depends(get_current_active_user)):
    """Manually trigger news sentiment analysis."""
    task = fetch_and_analyze_news.delay()
    return {"task_id": task.id, "status": "triggered", "task": "fetch_and_analyze_news"}


@router.post("/tasks/trigger-backtesting")
def trigger_backtesting(current_user: User = Depends(get_current_active_user)):
    """Manually trigger backtesting validation."""
    task = run_backtesting.delay()
    return {"task_id": task.id, "status": "triggered", "task": "run_backtesting"}


@router.post("/tasks/trigger-model-retrain")
def trigger_model_retrain(current_user: User = Depends(get_current_active_user)):
    """Manually trigger model retraining."""
    task = retrain_all_models.delay()
    return {"task_id": task.id, "status": "triggered", "task": "retrain_all_models"}