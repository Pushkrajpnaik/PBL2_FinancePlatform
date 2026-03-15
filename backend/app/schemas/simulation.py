from pydantic import BaseModel
from typing import Optional

class SimulationRequest(BaseModel):
    initial_investment: float
    monthly_sip: float
    time_horizon_years: int
    risk_profile: str                    # Conservative / Moderate / Aggressive
    target_amount: Optional[float] = None

class ScenarioOutput(BaseModel):
    worst_case: float
    below_average: float
    median: float
    above_average: float
    best_case: float

class RiskMetricsOutput(BaseModel):
    value_at_risk_95: float
    conditional_var_95: float
    probability_of_profit: float
    probability_of_doubling: float

class SimulationResponse(BaseModel):
    num_simulations: int
    time_horizon_years: int
    initial_investment: float
    monthly_sip: float
    total_invested: float
    scenarios: ScenarioOutput
    risk_metrics: RiskMetricsOutput
    expected_return_multiple: float
    goal_analysis: Optional[dict] = None