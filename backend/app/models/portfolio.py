from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    name                = Column(String, nullable=False)
    total_value         = Column(Float, default=0.0)
    target_allocation   = Column(JSON)   # {"equity": 40, "debt": 30, "gold": 20, "index": 10}
    current_allocation  = Column(JSON)   # actual current weights
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id              = Column(Integer, primary_key=True, index=True)
    portfolio_id    = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_type      = Column(String, nullable=False)   # mutual_fund / stock / etf / bond
    asset_code      = Column(String, nullable=False)   # fund code or ticker symbol
    asset_name      = Column(String, nullable=False)
    quantity        = Column(Float, nullable=False)
    avg_buy_price   = Column(Float, nullable=False)
    current_price   = Column(Float, default=0.0)
    current_value   = Column(Float, default=0.0)
    weight          = Column(Float, default=0.0)       # % of portfolio
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())