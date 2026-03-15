from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RiskProfileAnswers(BaseModel):
    financial_goal: int
    time_horizon: int
    loss_reaction: int
    income_stability: int
    investment_experience: int
    savings_rate: int
    emergency_fund: int
    max_acceptable_loss: int
    primary_motivation: int
    age_group: int

class RiskProfileResponse(BaseModel):
    id: int
    user_id: int
    score: float
    profile_type: str
    answers: dict
    created_at: datetime

    class Config:
        from_attributes = True

class RiskProfileResult(BaseModel):
    score: float
    profile_type: str
    description: str
    recommended_allocation: dict
    key_characteristics: list
