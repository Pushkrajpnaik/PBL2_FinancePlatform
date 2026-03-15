from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class RetirementPlan(Base):
    __tablename__ = "retirement_plans"

    id                          = Column(Integer, primary_key=True, index=True)
    user_id                     = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_age                 = Column(Integer, nullable=False)
    retirement_age              = Column(Integer, nullable=False)
    current_monthly_expenses    = Column(Float, nullable=False)
    expected_inflation_rate     = Column(Float, default=6.0)
    existing_savings            = Column(Float, default=0.0)
    required_corpus             = Column(Float, default=0.0)
    monthly_sip_required        = Column(Float, default=0.0)
    future_monthly_expense      = Column(Float, default=0.0)
    corpus_survival_probability = Column(Float, default=0.0)
    simulation_results          = Column(JSON)
    recommended_allocation      = Column(JSON)
    created_at                  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at                  = Column(DateTime(timezone=True), onupdate=func.now())