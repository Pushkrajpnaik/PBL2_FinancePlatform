from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.goal import Goal
from app.models.risk_profile import RiskProfile
from app.schemas.goal import GoalCreateRequest, GoalAnalysisResponse
from app.services.goal_service import analyze_goal, GOAL_TEMPLATES

router = APIRouter()


@router.get("/templates")
def get_goal_templates():
    """
    Returns all available goal types with descriptions.
    """
    return {
        "templates": [
            {
                "goal_type":        key,
                "name":             val["name"],
                "description":      val["description"],
                "icon":             val["icon"],
                "typical_horizon":  val["typical_horizon"],
            }
            for key, val in GOAL_TEMPLATES.items()
        ]
    }


@router.post("/analyze", response_model=GoalAnalysisResponse)
def analyze_goal_endpoint(
    request: GoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze a financial goal with Monte Carlo simulation.
    Returns success probability, required SIP, and recommendations.
    """
    result = analyze_goal(
        goal_type=request.goal_type,
        target_amount=request.target_amount,
        current_savings=request.current_savings,
        monthly_investment=request.monthly_investment,
        time_horizon_years=request.time_horizon_years,
        inflation_rate=request.inflation_rate / 100,
        risk_profile=request.risk_profile,
    )
    return result


@router.post("/save")
def save_goal(
    request: GoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze and save a financial goal to database.
    """
    result = analyze_goal(
        goal_type=request.goal_type,
        target_amount=request.target_amount,
        current_savings=request.current_savings,
        monthly_investment=request.monthly_investment,
        time_horizon_years=request.time_horizon_years,
        inflation_rate=request.inflation_rate / 100,
        risk_profile=request.risk_profile,
    )

    goal = Goal(
        user_id=current_user.id,
        goal_type=request.goal_type,
        goal_name=request.goal_name or result["goal_name"],
        target_amount=request.target_amount,
        current_savings=request.current_savings,
        monthly_investment=request.monthly_investment,
        time_horizon_years=request.time_horizon_years,
        inflation_rate=request.inflation_rate,
        success_probability=result["success_probability"],
        simulation_results=result["monte_carlo"],
        recommended_allocation={},
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return {
        "message":  "Goal saved successfully",
        "goal_id":  goal.id,
        "analysis": result,
    }


@router.get("/my-goals")
def get_my_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all saved goals for current user.
    """
    goals = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.status  == "active",
    ).all()

    return {
        "total_goals": len(goals),
        "goals": [
            {
                "id":                  g.id,
                "goal_type":           g.goal_type,
                "goal_name":           g.goal_name,
                "target_amount":       g.target_amount,
                "current_savings":     g.current_savings,
                "monthly_investment":  g.monthly_investment,
                "time_horizon_years":  g.time_horizon_years,
                "success_probability": g.success_probability,
                "status":              g.status,
                "created_at":          g.created_at,
            }
            for g in goals
        ],
    }


@router.get("/examples")
def get_goal_examples(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns pre-built example goals for different life stages.
    """
    return {
        "examples": [
            {
                "name":               "Buy a House in Mumbai",
                "goal_type":          "home_purchase",
                "target_amount":      5000000,
                "current_savings":    500000,
                "monthly_investment": 25000,
                "time_horizon_years": 7,
                "inflation_rate":     6.0,
                "risk_profile":       "Moderate",
            },
            {
                "name":               "Child's IIT/Medical Education",
                "goal_type":          "child_education",
                "target_amount":      3000000,
                "current_savings":    200000,
                "monthly_investment": 15000,
                "time_horizon_years": 12,
                "inflation_rate":     8.0,
                "risk_profile":       "Moderate",
            },
            {
                "name":               "Retirement at 60",
                "goal_type":          "retirement",
                "target_amount":      30000000,
                "current_savings":    1000000,
                "monthly_investment": 30000,
                "time_horizon_years": 25,
                "inflation_rate":     6.0,
                "risk_profile":       "Aggressive",
            },
            {
                "name":               "Emergency Fund",
                "goal_type":          "emergency_fund",
                "target_amount":      300000,
                "current_savings":    50000,
                "monthly_investment": 10000,
                "time_horizon_years": 2,
                "inflation_rate":     0.0,
                "risk_profile":       "Conservative",
            },
        ]
    }