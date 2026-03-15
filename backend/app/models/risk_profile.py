from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    score           = Column(Float, nullable=False)
    profile_type    = Column(String, nullable=False)  # Conservative / Moderate / Aggressive
    answers         = Column(JSON, nullable=False)     # raw questionnaire answers
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())