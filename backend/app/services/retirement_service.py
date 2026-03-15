import numpy as np
from typing import Dict
from app.ml.simulation.monte_carlo import (
    run_monte_carlo,
    calculate_goal_success_probability,
    RISK_PROFILE_ASSUMPTIONS,
)

# ---------------------------------------------------------------------------
# Retirement Phase Allocations
# ---------------------------------------------------------------------------
RETIREMENT_PHASES = {
    "accumulation": {
        "description": "Accumulation Phase — Building the corpus (20+ years to retirement)",
        "allocation": {
            "large_cap_equity":    30,
            "mid_cap_equity":      20,
            "index_funds":         20,
            "debt_funds":          15,
            "gold_etf":            10,
            "international_funds":  5,
        },
    },
    "transition": {
        "description": "Transition Phase — Consolidating gains (5-20 years to retirement)",
        "allocation": {
            "large_cap_equity": 30,
            "index_funds":      20,
            "debt_funds":       30,
            "hybrid_funds":     10,
            "gold_etf":         10,
        },
    },
    "pre_retirement": {
        "description": "Pre-Retirement Phase — Capital preservation (0-5 years to retirement)",
        "allocation": {
            "large_cap_equity": 15,
            "index_funds":      10,
            "debt_funds":       45,
            "liquid_funds":     20,
            "gold_etf":         10,
        },
    },
    "post_retirement": {
        "description": "Post-Retirement Phase — Income generation",
        "allocation": {
            "debt_funds":   50,
            "liquid_funds": 20,
            "gold_etf":     15,
            "index_funds":  15,
        },
    },
}


def get_retirement_phase(years_to_retirement: int) -> str:
    if years_to_retirement > 20:
        return "accumulation"
    elif years_to_retirement > 5:
        return "transition"
    elif years_to_retirement > 0:
        return "pre_retirement"
    else:
        return "post_retirement"


# ---------------------------------------------------------------------------
# Core Retirement Calculator
# ---------------------------------------------------------------------------
def calculate_retirement_plan(
    current_age:              int,
    retirement_age:           int,
    current_monthly_expenses: float,
    expected_inflation_rate:  float,
    existing_savings:         float,
    life_expectancy:          int   = 85,
    risk_profile:             str   = "Moderate",
) -> Dict:

    years_to_retirement   = retirement_age - current_age
    years_in_retirement   = life_expectancy - retirement_age

    if years_to_retirement <= 0:
        raise ValueError("Retirement age must be greater than current age")

    # ---------------------------------------------------------------------------
    # Step 1 — Calculate future monthly expenses at retirement
    # ---------------------------------------------------------------------------
    future_monthly_expense = current_monthly_expenses * (
        (1 + expected_inflation_rate) ** years_to_retirement
    )
    future_annual_expense = future_monthly_expense * 12

    # ---------------------------------------------------------------------------
    # Step 2 — Calculate required corpus using withdrawal rate
    # Corpus must last for entire retirement period
    # ---------------------------------------------------------------------------
    # Use 4% safe withdrawal rate as base, adjusted for Indian inflation
    post_retirement_return    = 0.08   # Conservative post-retirement return
    inflation_adjusted_return = (
        (1 + post_retirement_return) / (1 + expected_inflation_rate)
    ) - 1

    if inflation_adjusted_return > 0:
        required_corpus = future_annual_expense * (
            1 - (1 + inflation_adjusted_return) ** (-years_in_retirement)
        ) / inflation_adjusted_return
    else:
        required_corpus = future_annual_expense * years_in_retirement

    required_corpus = round(required_corpus, 2)

    # ---------------------------------------------------------------------------
    # Step 3 — Calculate required monthly SIP
    # ---------------------------------------------------------------------------
    assumptions     = RISK_PROFILE_ASSUMPTIONS.get(
        risk_profile, RISK_PROFILE_ASSUMPTIONS["Moderate"]
    )
    expected_return = assumptions["expected_annual_return"]
    volatility      = assumptions["annual_volatility"]
    monthly_rate    = expected_return / 12
    total_months    = years_to_retirement * 12

    # Future value of existing savings
    fv_existing = existing_savings * ((1 + monthly_rate) ** total_months)
    remaining   = required_corpus - fv_existing

    if remaining <= 0:
        required_sip = 0.0
    elif monthly_rate == 0:
        required_sip = remaining / total_months
    else:
        required_sip = remaining * monthly_rate / (
            ((1 + monthly_rate) ** total_months) - 1
        )

    required_sip = round(max(0, required_sip), 2)

    # ---------------------------------------------------------------------------
    # Step 4 — Monte Carlo simulation for corpus survival
    # ---------------------------------------------------------------------------
    mc_accumulation = run_monte_carlo(
        initial_investment    = existing_savings,
        monthly_sip           = required_sip,
        expected_annual_return= expected_return,
        annual_volatility     = volatility,
        time_horizon_years    = years_to_retirement,
    )

    # Corpus survival probability
    corpus_goal = calculate_goal_success_probability(
        initial_investment    = existing_savings,
        monthly_sip           = required_sip,
        expected_annual_return= expected_return,
        annual_volatility     = volatility,
        time_horizon_years    = years_to_retirement,
        target_amount         = required_corpus,
    )

    # ---------------------------------------------------------------------------
    # Step 5 — Retirement phase allocation
    # ---------------------------------------------------------------------------
    current_phase     = get_retirement_phase(years_to_retirement)
    phase_allocation  = RETIREMENT_PHASES[current_phase]

    # ---------------------------------------------------------------------------
    # Step 6 — Milestones
    # ---------------------------------------------------------------------------
    milestones = []
    for age in range(current_age + 5, retirement_age + 1, 5):
        years      = age - current_age
        months     = years * 12
        corpus_val = existing_savings * ((1 + monthly_rate) ** months)
        sip_val    = required_sip * (((1 + monthly_rate) ** months) - 1) / monthly_rate if monthly_rate > 0 else required_sip * months
        milestones.append({
            "age":            age,
            "years_invested": years,
            "projected_corpus": round(corpus_val + sip_val, 2),
            "phase":          get_retirement_phase(retirement_age - age),
        })

    return {
        "inputs": {
            "current_age":              current_age,
            "retirement_age":           retirement_age,
            "life_expectancy":          life_expectancy,
            "current_monthly_expenses": current_monthly_expenses,
            "inflation_rate":           expected_inflation_rate,
            "existing_savings":         existing_savings,
            "risk_profile":             risk_profile,
        },
        "results": {
            "years_to_retirement":          years_to_retirement,
            "years_in_retirement":          years_in_retirement,
            "future_monthly_expense":       round(future_monthly_expense, 2),
            "future_annual_expense":        round(future_annual_expense, 2),
            "required_corpus":              required_corpus,
            "required_monthly_sip":         required_sip,
            "corpus_achievement_probability": corpus_goal["success_probability"],
        },
        "monte_carlo": {
            "worst_case":    mc_accumulation["scenarios"]["worst_case"],
            "median":        mc_accumulation["scenarios"]["median"],
            "best_case":     mc_accumulation["scenarios"]["best_case"],
            "total_invested": mc_accumulation["total_invested"],
            "probability_of_profit": mc_accumulation["risk_metrics"]["probability_of_profit"],
        },
        "current_phase":      current_phase,
        "phase_details":      phase_allocation,
        "all_phases":         RETIREMENT_PHASES,
        "milestones":         milestones,
        "recommendation":     _get_retirement_recommendation(
            corpus_goal["success_probability"],
            required_sip,
            years_to_retirement,
        ),
    }


def _get_retirement_recommendation(
    success_prob: float,
    required_sip: float,
    years_to_retirement: int,
) -> Dict:
    if success_prob >= 80:
        return {
            "status":  "On Track",
            "color":   "green",
            "message": f"Your retirement plan is well-funded with {success_prob:.1f}% success probability. Keep investing consistently.",
        }
    elif success_prob >= 60:
        return {
            "status":  "Needs Review",
            "color":   "yellow",
            "message": f"Consider increasing your SIP by 10-15% annually to strengthen your retirement corpus.",
        }
    else:
        return {
            "status":  "At Risk",
            "color":   "red",
            "message": f"Your retirement corpus may be insufficient. Recommended SIP is ₹{required_sip:,.0f}/month. Start immediately — you have {years_to_retirement} years.",
        }