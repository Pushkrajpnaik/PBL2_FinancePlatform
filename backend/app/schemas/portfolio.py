from pydantic import BaseModel
from typing import Optional, Dict, List

class PortfolioOptimizationRequest(BaseModel):
    risk_profile: str                              # Conservative / Moderate / Aggressive
    method: str                                    # markowitz / risk_parity / cvar / black_litterman
    investment_amount: float
    investor_views: Optional[Dict[str, float]] = None

class OptimizationResult(BaseModel):
    method: str
    allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    investment_amount: Optional[float] = None
    allocated_amounts: Optional[Dict[str, float]] = None

class AllMethodsResult(BaseModel):
    risk_profile: str
    investment_amount: float
    markowitz: OptimizationResult
    risk_parity: OptimizationResult
    cvar: OptimizationResult
    black_litterman: OptimizationResult
    recommended: OptimizationResult