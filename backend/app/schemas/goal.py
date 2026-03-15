from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class GoalCreateRequest(BaseModel):
    goal_type:          str                     # home_purchase / child_education / retirement / emergency_fund / custom
    goal_name:          Optional[str] = None
    target_amount:      float
    current_savings:    float   = 0.0
    monthly_investment: float
    time_horizon_years: int
    inflation_rate:     float   = 6.0
    risk_profile:       str     = "Moderate"   # Conservative / Moderate / Aggressive

class GoalResponse(BaseModel):
    id:                          int
    user_id:                     int
    goal_type:                   str
    goal_name:                   str
    target_amount:               float
    current_savings:             float
    monthly_investment:          float
    time_horizon_years:          float
    inflation_rate:              float
    success_probability:         float
    status:                      str
    created_at:                  datetime

    class Config:
        from_attributes = True

class GoalAnalysisResponse(BaseModel):
    goal_type:                   str
    goal_name:                   str
    icon:                        str
    original_target:             float
    inflation_adjusted_target:   float
    inflation_rate:              float
    time_horizon_years:          int
    current_savings:             float
    monthly_investment:          float
    required_sip:                float
    sip_for_80_percent_success:  float
    risk_profile:                str
    success_probability:         float
    shortfall_risk:              float
    monte_carlo:                 dict
    recommendation:              dict