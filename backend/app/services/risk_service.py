from sqlalchemy.orm import Session
from app.models.risk_profile import RiskProfile
from app.schemas.risk_profile import RiskProfileAnswers, RiskProfileResult

SCORING_MAP = {
    "financial_goal":        {1: 5,  2: 10, 3: 18, 4: 25},
    "time_horizon":          {1: 2,  2: 5,  3: 10, 4: 16, 5: 20},
    "loss_reaction":         {1: 2,  2: 5,  3: 10, 4: 15},
    "income_stability":      {1: 2,  2: 5,  3: 8,  4: 10},
    "investment_experience": {1: 2,  2: 5,  3: 8,  4: 10},
    "savings_rate":          {1: 2,  2: 4,  3: 7,  4: 10},
    "emergency_fund":        {1: 2,  2: 4,  3: 7,  4: 10},
    "max_acceptable_loss":   {1: 2,  2: 5,  3: 8,  4: 10},
    "primary_motivation":    {1: 2,  2: 5,  3: 8,  4: 10},
    "age_group":             {1: 2,  2: 4,  3: 6,  4: 8,  5: 10},
}

PROFILE_CONFIG = {
    "Conservative": {
        "range": (0, 30),
        "description": "You prefer capital preservation over high returns. You are uncomfortable with losses and prefer stable, low-risk investments like debt funds and fixed deposits.",
        "recommended_allocation": {"debt_funds": 50, "liquid_funds": 20, "large_cap_equity": 15, "gold_etf": 10, "index_funds": 5},
        "key_characteristics": ["Low risk tolerance", "Prefers stable returns over high growth", "Short to medium investment horizon", "Prioritizes capital safety", "Suitable for: FDs, Debt Mutual Funds, Liquid Funds"],
    },
    "Moderate": {
        "range": (31, 60),
        "description": "You seek a balance between growth and stability. You can tolerate moderate losses in pursuit of better long-term returns and prefer a diversified portfolio.",
        "recommended_allocation": {"large_cap_equity": 25, "index_funds": 20, "hybrid_funds": 20, "debt_funds": 20, "gold_etf": 10, "mid_cap_equity": 5},
        "key_characteristics": ["Medium risk tolerance", "Balanced approach to growth and safety", "Medium to long investment horizon", "Comfortable with some market volatility", "Suitable for: Hybrid Funds, Index Funds, Balanced Portfolios"],
    },
    "Aggressive": {
        "range": (61, 100),
        "description": "You are focused on maximizing long-term wealth creation. You can tolerate significant short-term losses and volatility in pursuit of high long-term returns.",
        "recommended_allocation": {"mid_cap_equity": 25, "small_cap_equity": 20, "large_cap_equity": 20, "index_funds": 15, "international_funds": 10, "gold_etf": 5, "debt_funds": 5},
        "key_characteristics": ["High risk tolerance", "Long investment horizon (7+ years)", "Focused on wealth creation", "Comfortable with high market volatility", "Suitable for: Mid/Small Cap, International Funds, Direct Equity"],
    },
}

def calculate_risk_score(answers: RiskProfileAnswers) -> float:
    total_score = 0.0
    answers_dict = answers.model_dump()
    for field, value in answers_dict.items():
        if field in SCORING_MAP:
            total_score += SCORING_MAP[field].get(value, 0)
    max_possible = sum(max(v.values()) for v in SCORING_MAP.values())
    normalized = (total_score / max_possible) * 100
    return round(normalized, 2)

def get_profile_type(score: float) -> str:
    for profile, config in PROFILE_CONFIG.items():
        low, high = config["range"]
        if low <= score <= high:
            return profile
    return "Moderate"

def save_risk_profile(db: Session, user_id: int, answers: RiskProfileAnswers) -> RiskProfile:
    score = calculate_risk_score(answers)
    profile_type = get_profile_type(score)
    db.query(RiskProfile).filter(RiskProfile.user_id == user_id).delete()
    profile = RiskProfile(
        user_id=user_id,
        score=score,
        profile_type=profile_type,
        answers=answers.model_dump(),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def get_risk_result(score: float, profile_type: str) -> RiskProfileResult:
    config = PROFILE_CONFIG[profile_type]
    return RiskProfileResult(
        score=score,
        profile_type=profile_type,
        description=config["description"],
        recommended_allocation=config["recommended_allocation"],
        key_characteristics=config["key_characteristics"],
    )
