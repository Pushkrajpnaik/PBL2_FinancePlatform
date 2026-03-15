from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
from app.ml.regime.hmm_detector import (
    generate_placeholder_market_data,
    detect_regime_hmm,
    detect_regime_rule_based,
    adjust_portfolio_for_regime,
    REGIME_ALLOCATION_ADJUSTMENTS,
)
from app.ml.portfolio.optimizer import (
    mean_variance_optimization,
    get_assets_for_profile,
)

router = APIRouter()


@router.get("/market-regime")
def get_market_regime(
    current_user: User = Depends(get_current_active_user),
):
    """
    Detect current market regime using HMM.
    Returns regime type, confidence, and recommended action.
    """
    df     = generate_placeholder_market_data(days=500)
    result = detect_regime_hmm(df)
    return result


@router.get("/market-regime/history")
def get_regime_history(
    days: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns regime classification for last N days.
    """
    df = generate_placeholder_market_data(days=500)
    df_recent = df.tail(days).copy()

    history = []
    for _, row in df_recent.iterrows():
        history.append({
            "date":       row["date"].strftime("%Y-%m-%d"),
            "close":      round(float(row["close"]), 2),
            "returns":    round(float(row["returns"]) * 100, 4),
            "volatility": round(float(row["volatility"]) * 100, 4),
            "momentum":   round(float(row["momentum"]) * 100, 4),
        })

    return {
        "days":    days,
        "history": history,
    }


@router.get("/regime-adjusted-portfolio")
def get_regime_adjusted_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns portfolio allocation dynamically adjusted
    for current market regime.
    """
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found. Please complete risk assessment first."
        )

    # Get base portfolio
    assets          = get_assets_for_profile(profile.profile_type)
    base_result     = mean_variance_optimization(assets)
    base_allocation = base_result["allocation"]

    # Detect current regime
    df     = generate_placeholder_market_data(days=500)
    regime = detect_regime_hmm(df)

    # Adjust portfolio for regime
    adjusted_allocation = adjust_portfolio_for_regime(
        base_allocation,
        regime["regime"],
    )

    adjustment = REGIME_ALLOCATION_ADJUSTMENTS.get(
        regime["regime"],
        REGIME_ALLOCATION_ADJUSTMENTS["Sideways/Neutral"],
    )

    return {
        "regime_detection":       regime,
        "base_allocation":        base_allocation,
        "adjusted_allocation":    adjusted_allocation,
        "adjustment_description": adjustment["description"],
    }