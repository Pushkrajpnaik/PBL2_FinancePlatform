import numpy as np
from typing import Dict
from app.ml.simulation.monte_carlo import (
    run_monte_carlo,
    calculate_goal_success_probability,
    RISK_PROFILE_ASSUMPTIONS,
)

# ---------------------------------------------------------------------------
# Goal Templates
# ---------------------------------------------------------------------------
GOAL_TEMPLATES = {
    "home_purchase": {
        "name":        "Home Purchase",
        "description": "Save for buying a house or apartment",
        "icon":        "🏠",
        "typical_horizon": 7,
        "inflation_sensitive": True,
    },
    "child_education": {
        "name":        "Child's Education",
        "description": "Save for your child's higher education",
        "icon":        "🎓",
        "typical_horizon": 15,
        "inflation_sensitive": True,
    },
    "retirement": {
        "name":        "Retirement",
        "description": "Build a retirement corpus",
        "icon":        "🏖️",
        "typical_horizon": 25,
        "inflation_sensitive": True,
    },
    "emergency_fund": {
        "name":        "Emergency Fund",
        "description": "Build 6 months of expenses as safety net",
        "icon":        "🆘",
        "typical_horizon": 2,
        "inflation_sensitive": False,
    },
    "vehicle_purchase": {
        "name":        "Vehicle Purchase",
        "description": "Save for buying a car or bike",
        "icon":        "🚗",
        "typical_horizon": 3,
        "inflation_sensitive": False,
    },
    "travel": {
        "name":        "Travel / Vacation",
        "description": "Save for a dream vacation",
        "icon":        "✈️",
        "typical_horizon": 2,
        "inflation_sensitive": False,
    },
    "custom": {
        "name":        "Custom Goal",
        "description": "Any custom financial goal",
        "icon":        "🎯",
        "typical_horizon": 5,
        "inflation_sensitive": True,
    },
}


# ---------------------------------------------------------------------------
# Inflation Adjustment
# ---------------------------------------------------------------------------
def inflation_adjusted_amount(
    amount: float,
    years: float,
    inflation_rate: float = 0.06,
) -> float:
    return round(amount * ((1 + inflation_rate) ** years), 2)


# ---------------------------------------------------------------------------
# SIP Calculator
# ---------------------------------------------------------------------------
def calculate_required_sip(
    target_amount: float,
    current_savings: float,
    expected_annual_return: float,
    time_horizon_years: int,
) -> float:
    """
    Calculates monthly SIP required to reach target amount.
    """
    monthly_rate  = expected_annual_return / 12
    total_months  = time_horizon_years * 12

    # Future value of current savings
    fv_savings = current_savings * ((1 + monthly_rate) ** total_months)

    # Remaining amount needed from SIP
    remaining = target_amount - fv_savings

    if remaining <= 0:
        return 0.0

    # SIP formula: PMT = FV * r / ((1+r)^n - 1)
    if monthly_rate == 0:
        sip = remaining / total_months
    else:
        sip = remaining * monthly_rate / (((1 + monthly_rate) ** total_months) - 1)

    return round(max(0, sip), 2)


# ---------------------------------------------------------------------------
# Full Goal Analysis
# ---------------------------------------------------------------------------
def analyze_goal(
    goal_type: str,
    target_amount: float,
    current_savings: float,
    monthly_investment: float,
    time_horizon_years: int,
    inflation_rate: float,
    risk_profile: str,
) -> Dict:
    assumptions = RISK_PROFILE_ASSUMPTIONS.get(
        risk_profile,
        RISK_PROFILE_ASSUMPTIONS["Moderate"]
    )

    expected_return = assumptions["expected_annual_return"]
    volatility      = assumptions["annual_volatility"]

    # Inflation adjusted target
    template = GOAL_TEMPLATES.get(goal_type, GOAL_TEMPLATES["custom"])
    if template["inflation_sensitive"]:
        inflation_adjusted_target = inflation_adjusted_amount(
            target_amount,
            time_horizon_years,
            inflation_rate,
        )
    else:
        inflation_adjusted_target = target_amount

    # Required SIP
    required_sip = calculate_required_sip(
        target_amount=inflation_adjusted_target,
        current_savings=current_savings,
        expected_annual_return=expected_return,
        time_horizon_years=time_horizon_years,
    )

    # Monte Carlo simulation
    mc_results = run_monte_carlo(
        initial_investment=current_savings,
        monthly_sip=monthly_investment,
        expected_annual_return=expected_return,
        annual_volatility=volatility,
        time_horizon_years=time_horizon_years,
    )

    # Goal success probability
    goal_analysis = calculate_goal_success_probability(
        initial_investment=current_savings,
        monthly_sip=monthly_investment,
        expected_annual_return=expected_return,
        annual_volatility=volatility,
        time_horizon_years=time_horizon_years,
        target_amount=inflation_adjusted_target,
    )

    # SIP needed to achieve 80% success probability
    sip_for_80_percent = calculate_required_sip(
        target_amount=inflation_adjusted_target,
        current_savings=current_savings,
        expected_annual_return=expected_return * 0.85,
        time_horizon_years=time_horizon_years,
    )

    return {
        "goal_type":                  goal_type,
        "goal_name":                  template["name"],
        "icon":                       template["icon"],
        "original_target":            target_amount,
        "inflation_adjusted_target":  inflation_adjusted_target,
        "inflation_rate":             inflation_rate,
        "time_horizon_years":         time_horizon_years,
        "current_savings":            current_savings,
        "monthly_investment":         monthly_investment,
        "required_sip":               required_sip,
        "sip_for_80_percent_success": sip_for_80_percent,
        "risk_profile":               risk_profile,
        "success_probability":        goal_analysis["success_probability"],
        "shortfall_risk":             goal_analysis["shortfall_risk"],
        "monte_carlo": {
            "worst_case":    mc_results["scenarios"]["worst_case"],
            "median":        mc_results["scenarios"]["median"],
            "best_case":     mc_results["scenarios"]["best_case"],
            "total_invested": mc_results["total_invested"],
        },
        "recommendation": _get_recommendation(
            goal_analysis["success_probability"],
            monthly_investment,
            required_sip,
        ),
    }


def _get_recommendation(
    success_prob: float,
    current_sip: float,
    required_sip: float,
) -> Dict:
    if success_prob >= 80:
        return {
            "status":  "On Track",
            "color":   "green",
            "message": f"Your current investment of ₹{current_sip:,.0f}/month gives you a strong {success_prob:.1f}% chance of achieving this goal.",
        }
    elif success_prob >= 60:
        gap = required_sip - current_sip
        return {
            "status":  "Needs Attention",
            "color":   "yellow",
            "message": f"Increase your monthly SIP by ₹{gap:,.0f} to improve goal success probability.",
        }
    else:
        gap = required_sip - current_sip
        return {
            "status":  "At Risk",
            "color":   "red",
            "message": f"Your goal is at risk. Increase monthly SIP by ₹{gap:,.0f} or extend your time horizon.",
        }