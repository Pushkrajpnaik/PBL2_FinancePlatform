from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
from app.models.retirement import RetirementPlan
from app.schemas.retirement import RetirementRequest, RetirementResponse
from app.services.retirement_service import (
    calculate_retirement_plan,
    RETIREMENT_PHASES,
)

router = APIRouter()


@router.post("/calculate", response_model=RetirementResponse)
def calculate_retirement(
    request: RetirementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate complete retirement plan with corpus requirement,
    required SIP, Monte Carlo survival probability and phase-wise allocation.
    """
    if request.retirement_age <= request.current_age:
        raise HTTPException(
            status_code=400,
            detail="Retirement age must be greater than current age"
        )
    if request.life_expectancy <= request.retirement_age:
        raise HTTPException(
            status_code=400,
            detail="Life expectancy must be greater than retirement age"
        )

    result = calculate_retirement_plan(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        current_monthly_expenses=request.current_monthly_expenses,
        expected_inflation_rate=request.expected_inflation_rate / 100,
        existing_savings=request.existing_savings,
        life_expectancy=request.life_expectancy,
        risk_profile=request.risk_profile,
    )
    return result


@router.post("/save")
def save_retirement_plan(
    request: RetirementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate and save retirement plan to database.
    """
    result = calculate_retirement_plan(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        current_monthly_expenses=request.current_monthly_expenses,
        expected_inflation_rate=request.expected_inflation_rate / 100,
        existing_savings=request.existing_savings,
        life_expectancy=request.life_expectancy,
        risk_profile=request.risk_profile,
    )

    plan = RetirementPlan(
        user_id=current_user.id,
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        current_monthly_expenses=request.current_monthly_expenses,
        expected_inflation_rate=request.expected_inflation_rate,
        existing_savings=request.existing_savings,
        required_corpus=result["results"]["required_corpus"],
        monthly_sip_required=result["results"]["required_monthly_sip"],
        future_monthly_expense=result["results"]["future_monthly_expense"],
        corpus_survival_probability=result["results"]["corpus_achievement_probability"],
        simulation_results=result["monte_carlo"],
        recommended_allocation=result["phase_details"]["allocation"],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "message": "Retirement plan saved successfully",
        "plan_id": plan.id,
        "results": result,
    }


@router.get("/phases")
def get_retirement_phases(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns all retirement phases with recommended allocations.
    """
    return {"phases": RETIREMENT_PHASES}


@router.get("/my-plan")
def get_my_retirement_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get saved retirement plan for current user.
    """
    plan = db.query(RetirementPlan).filter(
        RetirementPlan.user_id == current_user.id
    ).order_by(RetirementPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No retirement plan found. Please calculate one first."
        )

    return {
        "id":                           plan.id,
        "current_age":                  plan.current_age,
        "retirement_age":               plan.retirement_age,
        "required_corpus":              plan.required_corpus,
        "monthly_sip_required":         plan.monthly_sip_required,
        "future_monthly_expense":       plan.future_monthly_expense,
        "corpus_survival_probability":  plan.corpus_survival_probability,
        "recommended_allocation":       plan.recommended_allocation,
        "created_at":                   plan.created_at,
    }