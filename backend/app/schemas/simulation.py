from pydantic import BaseModel, validator
from typing import Optional


class SimulationRequest(BaseModel):
    # ✅ Backend field names — frontend must map to these:
    #   current_savings    → initial_investment
    #   monthly_investment → monthly_sip
    initial_investment: float
    monthly_sip: float
    time_horizon_years: int
    risk_profile: str                     # "Conservative" | "Moderate" | "Aggressive"
    target_amount: Optional[float] = None

    @validator("risk_profile")
    def validate_risk_profile(cls, v):
        allowed = {"Conservative", "Moderate", "Aggressive"}
        if v not in allowed:
            raise ValueError(f"risk_profile must be one of: {', '.join(allowed)}")
        return v

    @validator("time_horizon_years")
    def validate_time_horizon(cls, v):
        if v < 1 or v > 50:
            raise ValueError("time_horizon_years must be between 1 and 50")
        return v

    @validator("initial_investment", "monthly_sip")
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class ScenarioOutput(BaseModel):
    worst_case:    float
    below_average: float
    median:        float
    above_average: float
    best_case:     float


class RiskMetricsOutput(BaseModel):
    value_at_risk_95:        float
    conditional_var_95:      float
    probability_of_profit:   float
    probability_of_doubling: float


class GoalAnalysisOutput(BaseModel):
    target_amount:       float
    success_probability: float
    median_outcome:      float
    worst_case:          float
    best_case:           float
    shortfall_risk:      float


class SimulationResponse(BaseModel):
    num_simulations:         int
    time_horizon_years:      int
    initial_investment:      float
    monthly_sip:             float
    total_invested:          float
    scenarios:               ScenarioOutput
    risk_metrics:            RiskMetricsOutput
    expected_return_multiple: float
    goal_analysis:           Optional[GoalAnalysisOutput] = None  # present when target_amount supplied