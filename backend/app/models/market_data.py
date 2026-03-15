from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from app.core.database import Base

class MutualFundNAV(Base):
    __tablename__ = "mutual_fund_nav"

    id          = Column(Integer, primary_key=True, index=True)
    scheme_code = Column(String, index=True, nullable=False)
    scheme_name = Column(String, nullable=False)
    nav         = Column(Float, nullable=False)
    nav_date    = Column(Date, nullable=False)
    fund_type   = Column(String)   # equity / debt / hybrid / index
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id          = Column(Integer, primary_key=True, index=True)
    symbol      = Column(String, index=True, nullable=False)
    exchange    = Column(String, nullable=False)   # NSE / BSE
    open_price  = Column(Float)
    high_price  = Column(Float)
    low_price   = Column(Float)
    close_price = Column(Float, nullable=False)
    volume      = Column(Float)
    price_date  = Column(Date, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class MarketIndex(Base):
    __tablename__ = "market_indices"

    id          = Column(Integer, primary_key=True, index=True)
    index_name  = Column(String, index=True, nullable=False)  # NIFTY50 / SENSEX
    open_price  = Column(Float)
    high_price  = Column(Float)
    low_price   = Column(Float)
    close_price = Column(Float, nullable=False)
    index_date  = Column(Date, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())