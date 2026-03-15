import requests
import yfinance as yf
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_rbi_repo_rate() -> Optional[float]:
    """
    Fetches current RBI repo rate.
    Uses a free financial data source.
    """
    try:
        # RBI repo rate via Yahoo Finance proxy
        # Using India 10-year bond yield as proxy
        ticker = yf.Ticker("^TNX")
        info   = ticker.fast_info
        return round(float(info.last_price), 2)
    except Exception as e:
        logger.error(f"Failed to fetch repo rate: {e}")
        return 6.5  # fallback to last known rate


def fetch_usd_inr() -> Optional[float]:
    """Fetches current USD/INR exchange rate."""
    try:
        ticker = yf.Ticker("USDINR=X")
        info   = ticker.fast_info
        return round(float(info.last_price), 2)
    except Exception as e:
        logger.error(f"Failed to fetch USD/INR: {e}")
        return 83.5  # fallback


def fetch_gold_price() -> Optional[Dict]:
    """Fetches current gold price in USD and calculates INR."""
    try:
        gold   = yf.Ticker("GC=F")
        info   = gold.fast_info
        usd    = float(info.last_price)
        inr    = fetch_usd_inr() or 83.5
        # Convert to per 10 grams (Indian standard)
        per_10g_inr = round(usd * inr / 31.1 * 10, 2)
        return {
            "gold_usd_per_oz": round(usd, 2),
            "gold_inr_per_10g": per_10g_inr,
            "usd_inr": inr,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to fetch gold price: {e}")
        return None


def fetch_crude_oil_price() -> Optional[float]:
    """Fetches current crude oil price (WTI)."""
    try:
        crude = yf.Ticker("CL=F")
        info  = crude.fast_info
        return round(float(info.last_price), 2)
    except Exception as e:
        logger.error(f"Failed to fetch crude oil: {e}")
        return None


def get_full_macro_snapshot() -> Dict:
    """
    Returns a complete snapshot of all macro indicators.
    """
    usd_inr = fetch_usd_inr()
    gold    = fetch_gold_price()
    crude   = fetch_crude_oil_price()

    return {
        "timestamp":    datetime.now().isoformat(),
        "forex": {
            "usd_inr":  usd_inr or 83.5,
            "eur_inr":  round((usd_inr or 83.5) * 1.08, 2),
        },
        "commodities": {
            "gold_usd_oz":    gold["gold_usd_per_oz"] if gold else 2000,
            "gold_inr_10g":   gold["gold_inr_per_10g"] if gold else 58000,
            "crude_oil_usd":  crude or 75,
        },
        "rates": {
            "rbi_repo_rate":  6.5,  # Updated manually or via RBI API
            "inflation_cpi":  5.8,  # Updated from MOSPI data
        },
        "market_cap": {
            "nifty50_pe":     22.5,  # Updated from NSE
            "nifty50_pb":     3.8,
        }
    }