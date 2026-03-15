from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Goal(Base):
    __tablename__ = "goals"

    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_type               = Column(String, nullable=False)  # home / education / retirement / emergency / custom
    goal_name               = Column(String, nullable=False)
    target_amount           = Column(Float, nullable=False)
    current_savings         = Column(Float, default=0.0)
    monthly_investment      = Column(Float, default=0.0)
    time_horizon_years      = Column(Float, nullable=False)
    inflation_rate          = Column(Float, default=6.0)
    success_probability     = Column(Float, default=0.0)      # from Monte Carlo
    simulation_results      = Column(JSON)                    # full MC output
    recommended_allocation  = Column(JSON)                    # suggested portfolio mix
    status                  = Column(String, default="active")
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
    updated_at              = Column(DateTime(timezone=True), onupdate=func.now())