from pydantic import BaseModel
from typing import Optional

class RetirementRequest(BaseModel):
    current_age:              int
    retirement_age:           int
    current_monthly_expenses: float
    expected_inflation_rate:  float = 6.0
    existing_savings:         float = 0.0
    life_expectancy:          int   = 85
    risk_profile:             str   = "Moderate"

class RetirementResponse(BaseModel):
    inputs:       dict
    results:      dict
    monte_carlo:  dict
    current_phase: str
    phase_details: dict
    all_phases:   dict
    milestones:   list
    recommendation: dict