import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators from OHLCV data.
    Used for ML feature engineering.
    """
    if df is None or df.empty:
        return df

    # Trend indicators
    df["sma_20"]  = df["close"].rolling(20, min_periods=1).mean()
    df["sma_50"]  = df["close"].rolling(50, min_periods=1).mean()
    df["sma_200"] = df["close"].rolling(200, min_periods=1).mean()
    df["ema_12"]  = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"]  = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"]    = df["ema_12"] - df["ema_26"]

    # Momentum indicators
    delta        = df["close"].diff()
    gain         = delta.clip(lower=0)
    loss         = -delta.clip(upper=0)
    avg_gain     = gain.rolling(14, min_periods=1).mean()
    avg_loss     = loss.rolling(14, min_periods=1).mean()
    rs           = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"]    = 100 - (100 / (1 + rs))
    df["rsi"]    = df["rsi"].fillna(50)

    # Volatility indicators
    df["bb_mid"]   = df["close"].rolling(20, min_periods=1).mean()
    bb_std         = df["close"].rolling(20, min_periods=1).std()
    df["bb_upper"] = df["bb_mid"] + (bb_std * 2)
    df["bb_lower"] = df["bb_mid"] - (bb_std * 2)
    df["atr"]      = calculate_atr(df)

    # Volume indicators
    df["volume_sma"] = df["volume"].rolling(20, min_periods=1).mean()
    df["volume_ratio"] = df["volume"] / df["volume_sma"].replace(0, np.nan)
    df["volume_ratio"] = df["volume_ratio"].fillna(1)

    # Trend signals
    df["trend_signal"] = np.where(
        df["sma_20"] > df["sma_50"], 1,
        np.where(df["sma_20"] < df["sma_50"], -1, 0)
    )

    return df.fillna(0)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range."""
    high_low   = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close  = abs(df["low"] - df["close"].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period, min_periods=1).mean()


def calculate_correlation_matrix(
    price_data: Dict[str, pd.DataFrame],
) -> Dict:
    """
    Calculates real correlation matrix from historical price data.
    Replaces hardcoded correlation values in optimizer.
    """
    returns_data = {}
    for symbol, df in price_data.items():
        if df is not None and not df.empty and "returns" in df.columns:
            returns_data[symbol] = df["returns"].replace(0, np.nan).dropna()

    if len(returns_data) < 2:
        return {}

    returns_df   = pd.DataFrame(returns_data).dropna()
    corr_matrix  = returns_df.corr()

    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "calculated_at":      datetime.now().isoformat(),
        "data_points":        len(returns_df),
        "symbols":            list(returns_data.keys()),
    }


def calculate_real_asset_stats(
    price_data: Dict[str, pd.DataFrame],
) -> Dict:
    """
    Calculates real expected returns and volatilities
    from historical price data.
    Replaces hardcoded PLACEHOLDER_ASSETS values.
    """
    stats = {}
    for symbol, df in price_data.items():
        if df is None or df.empty:
            continue
        returns    = df["returns"].replace(0, np.nan).dropna()
        if len(returns) < 10:
            continue
        annual_return = float(returns.mean() * 252)
        annual_vol    = float(returns.std() * np.sqrt(252))
        stats[symbol] = {
            "expected_return": round(annual_return, 4),
            "volatility":      round(annual_vol, 4),
            "data_points":     len(returns),
            "calculated_at":   datetime.now().isoformat(),
        }
    return stats


def detect_market_regime_from_data(df: pd.DataFrame) -> Dict:
    """
    Detects market regime from real price data.
    Returns regime signal for portfolio adjustment.
    """
    if df is None or df.empty or len(df) < 20:
        return {"regime": "Unknown", "confidence": 0}

    recent      = df.tail(20)
    avg_return  = float(recent["returns"].mean())
    avg_vol     = float(recent["volatility"].mean()) if "volatility" in recent.columns else 0
    momentum    = float(df["close"].iloc[-1] / df["close"].iloc[-20] - 1) if len(df) >= 20 else 0

    if avg_return > 0.0005 and momentum > 0.02:
        regime     = "Bull Market"
        confidence = min(95, 70 + abs(momentum) * 100)
        color      = "green"
        action     = "Increase equity exposure"
    elif avg_return < -0.0003 and momentum < -0.02:
        regime     = "Bear Market"
        confidence = min(95, 70 + abs(momentum) * 100)
        color      = "red"
        action     = "Rotate to defensive assets"
    elif avg_vol > 0.015:
        regime     = "High Volatility"
        confidence = min(95, 65 + avg_vol * 1000)
        color      = "yellow"
        action     = "Reduce risk exposure"
    elif avg_return > 0.0002 and momentum > 0:
        regime     = "Recovery"
        confidence = 70.0
        color      = "blue"
        action     = "Gradually re-enter equities"
    else:
        regime     = "Sideways/Neutral"
        confidence = 60.0
        color      = "gray"
        action     = "Maintain current allocation"

    return {
        "regime":          regime,
        "confidence":      round(confidence, 2),
        "color":           color,
        "action":          action,
        "avg_return":      round(avg_return * 100, 4),
        "avg_volatility":  round(avg_vol * 100, 4),
        "momentum":        round(momentum * 100, 4),
        "detection_method": "Rule-Based on Real Data",
        "calculated_at":   datetime.now().isoformat(),
    }


def process_news_for_portfolio_signal(
    news_sentiment: Dict,
    current_regime: str,
) -> Dict:
    """
    Converts news sentiment into portfolio adjustment signal.
    This is the news → portfolio pipeline!
    """
    overall_score    = news_sentiment.get("overall_score", 0)
    sector_sentiment = news_sentiment.get("sector_sentiment", {})
    risk_level       = news_sentiment.get("risk_level", {}).get("level", "Neutral")

    # Base adjustment from news sentiment
    if overall_score < -0.3 or risk_level == "High":
        news_signal        = "REDUCE_RISK"
        equity_adjustment  = -0.10
        debt_adjustment    = +0.10
        confidence         = min(90, 60 + abs(overall_score) * 50)
    elif overall_score > 0.3:
        news_signal        = "INCREASE_RISK"
        equity_adjustment  = +0.05
        debt_adjustment    = -0.05
        confidence         = min(85, 55 + overall_score * 50)
    else:
        news_signal        = "NEUTRAL"
        equity_adjustment  = 0
        debt_adjustment    = 0
        confidence         = 50.0

    # Sector-specific signals
    sector_signals = {}
    for sector, data in sector_sentiment.items():
        if isinstance(data, dict):
            score = data.get("avg_score", 0)
            if score > 0.2:
                sector_signals[sector] = "OVERWEIGHT"
            elif score < -0.2:
                sector_signals[sector] = "UNDERWEIGHT"
            else:
                sector_signals[sector] = "NEUTRAL"

    # Combine with regime
    regime_multiplier = {
        "Bull Market":      1.2,
        "Bear Market":      0.8,
        "High Volatility":  0.7,
        "Recovery":         1.0,
        "Sideways/Neutral": 1.0,
    }.get(current_regime, 1.0)

    final_equity_adj = round(equity_adjustment * regime_multiplier, 3)

    return {
        "news_signal":         news_signal,
        "overall_news_score":  round(overall_score, 4),
        "equity_adjustment":   final_equity_adj,
        "debt_adjustment":     round(debt_adjustment, 3),
        "confidence":          round(confidence, 2),
        "sector_signals":      sector_signals,
        "risk_level":          risk_level,
        "current_regime":      current_regime,
        "regime_multiplier":   regime_multiplier,
        "recommendation":      _get_news_recommendation(news_signal, final_equity_adj),
        "calculated_at":       datetime.now().isoformat(),
    }


def _get_news_recommendation(signal: str, equity_adj: float) -> str:
    if signal == "REDUCE_RISK":
        return f"News sentiment is negative. Reduce equity by {abs(equity_adj)*100:.0f}% and increase debt allocation."
    elif signal == "INCREASE_RISK":
        return f"News sentiment is positive. Consider increasing equity by {equity_adj*100:.0f}%."
    else:
        return "News sentiment is neutral. Maintain current allocation."