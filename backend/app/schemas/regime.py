from pydantic import BaseModel
from typing import Optional, Dict

class RegimeResponse(BaseModel):
    regime: str
    regime_id: int
    confidence: float
    description: str
    action: str
    color: str
    detection_method: Optional[str] = None
    transition_probabilities: Optional[Dict[str, float]] = None

class RegimeWithPortfolioResponse(BaseModel):
    regime_detection: dict
    base_allocation: Dict[str, float]
    adjusted_allocation: Dict[str, float]
    adjustment_description: str