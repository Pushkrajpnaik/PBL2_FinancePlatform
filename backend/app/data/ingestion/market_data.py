import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indian Market Symbols for Yahoo Finance
# ---------------------------------------------------------------------------
INDIAN_INDICES = {
    "NIFTY50":   "^NSEI",
    "SENSEX":    "^BSESN",
    "NIFTYBANK": "^NSEBANK",
    "NIFTYMID":  "NIFTY_MID_SELECT.NS",
}

INDIAN_STOCKS = {
    "RELIANCE":   "RELIANCE.NS",
    "TCS":        "TCS.NS",
    "HDFCBANK":   "HDFCBANK.NS",
    "INFY":       "INFY.NS",
    "ICICIBANK":  "ICICIBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "SBIN":       "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK":  "KOTAKBANK.NS",
    "LT":         "LT.NS",
}

COMMODITY_SYMBOLS = {
    "GOLD":   "GC=F",
    "CRUDE":  "CL=F",
    "SILVER": "SI=F",
}

FOREX_SYMBOLS = {
    "USD_INR": "USDINR=X",
    "EUR_INR": "EURINR=X",
    "GBP_INR": "GBPINR=X",
}

GLOBAL_INDICES = {
    "SP500":  "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW":    "^DJI",
    "NIKKEI": "^N225",
}

# ---------------------------------------------------------------------------
# Core Data Fetcher
# ---------------------------------------------------------------------------
def fetch_price_history(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
) -> Optional[pd.DataFrame]:
    """
    Fetches historical price data from Yahoo Finance.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        ticker = yf.Ticker(symbol)
        df     = ticker.history(period=period, interval=interval)
        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None

        df.index   = pd.to_datetime(df.index)
        df         = df[["Open", "High", "Low", "Close", "Volume"]]
        df.columns = ["open", "high", "low", "close", "volume"]

        n = len(df)

        # Use min_periods=1 so short periods don't return empty
        df["returns"]    = df["close"].pct_change()
        df["volatility"] = df["returns"].rolling(min(20, n), min_periods=1).std()
        df["momentum"]   = df["close"].pct_change(min(20, n - 1))
        df["sma_50"]     = df["close"].rolling(min(50, n), min_periods=1).mean()
        df["sma_200"]    = df["close"].rolling(min(200, n), min_periods=1).mean()

        # Fill any remaining NaN with 0
        df = df.fillna(0)

        logger.info(f"Fetched {len(df)} rows for {symbol}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")
        return None


def fetch_current_price(symbol: str) -> Optional[Dict]:
    """Fetches current/latest price for a symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.fast_info
        return {
            "symbol":         symbol,
            "current_price":  round(float(info.last_price), 2),
            "previous_close": round(float(info.previous_close), 2),
            "change":         round(float(info.last_price - info.previous_close), 2),
            "change_pct":     round(float((info.last_price - info.previous_close) / info.previous_close * 100), 2),
            "timestamp":      datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to fetch current price for {symbol}: {e}")
        return None


def fetch_nifty50_history(period: str = "2y") -> Optional[pd.DataFrame]:
    """Fetches NIFTY50 historical data."""
    return fetch_price_history("^NSEI", period=period)


def fetch_multiple_stocks(
    symbols: List[str],
    period: str = "1y",
) -> Dict[str, pd.DataFrame]:
    """Fetches data for multiple symbols."""
    results = {}
    for symbol in symbols:
        df = fetch_price_history(symbol, period=period)
        if df is not None:
            results[symbol] = df
    return results


def calculate_returns_stats(df: pd.DataFrame) -> Dict:
    """Calculates return statistics from price history."""
    if df is None or df.empty:
        return {}
    try:
        returns = df["returns"].replace(0, np.nan).dropna()
        if returns.empty:
            return {}
        annual_return = float(returns.mean() * 252 * 100)
        annual_vol    = float(returns.std() * np.sqrt(252) * 100)
        sharpe        = (annual_return - 6) / annual_vol if annual_vol > 0 else 0
        cumulative    = (1 + returns).cumprod()
        peak          = cumulative.cummax()
        drawdown      = ((cumulative - peak) / peak * 100).min()
        return {
            "annual_return":     round(annual_return, 2),
            "annual_volatility": round(annual_vol, 2),
            "sharpe_ratio":      round(sharpe, 3),
            "max_drawdown":      round(float(drawdown), 2),
            "total_return":      round(float((cumulative.iloc[-1] - 1) * 100), 2),
            "data_points":       len(returns),
        }
    except Exception as e:
        logger.error(f"Failed to calculate stats: {e}")
        return {}


def get_market_summary() -> Dict:
    """Gets a quick summary of key Indian market indicators."""
    summary = {}
    key_symbols = {
        "NIFTY50":   "^NSEI",
        "SENSEX":    "^BSESN",
        "GOLD":      "GC=F",
        "USD_INR":   "USDINR=X",
        "CRUDE_OIL": "CL=F",
    }
    for name, symbol in key_symbols.items():
        price = fetch_current_price(symbol)
        if price:
            summary[name] = {
                "price":      price["current_price"],
                "change_pct": price["change_pct"],
                "direction":  "up" if price["change_pct"] > 0 else "down",
            }
    return summary