import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Real Asset Symbols mapped to Yahoo Finance
# ---------------------------------------------------------------------------
ASSET_SYMBOLS = {
    # Equity
    "large_cap_equity":    ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"],
    "mid_cap_equity":      ["PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "MPHASIS.NS"],
    "small_cap_equity":    ["HAPPSTMNDS.NS", "NAZARA.NS", "ROUTE.NS"],
    "index_funds":         ["^NSEI"],
    "international_funds": ["^GSPC"],
    # Debt proxy
    "debt_funds":          ["^TNX"],
    # Hybrid proxy
    "hybrid_funds":        ["^NSEI", "^TNX"],
    # Gold
    "gold_etf":            ["GC=F"],
    # Liquid
    "liquid_funds":        ["^IRX"],
}

# Fallback returns if real data unavailable
FALLBACK_RETURNS = {
    "large_cap_equity":    {"expected_return": 0.14, "volatility": 0.18},
    "mid_cap_equity":      {"expected_return": 0.16, "volatility": 0.22},
    "small_cap_equity":    {"expected_return": 0.18, "volatility": 0.28},
    "index_funds":         {"expected_return": 0.13, "volatility": 0.16},
    "international_funds": {"expected_return": 0.12, "volatility": 0.20},
    "debt_funds":          {"expected_return": 0.07, "volatility": 0.04},
    "hybrid_funds":        {"expected_return": 0.10, "volatility": 0.10},
    "liquid_funds":        {"expected_return": 0.06, "volatility": 0.01},
    "gold_etf":            {"expected_return": 0.09, "volatility": 0.15},
}


def fetch_real_asset_returns(
    assets: List[str],
    period: str = "2y",
) -> Dict[str, Dict]:
    """
    Fetches real historical returns for each asset class.
    Uses representative ETF/index as proxy for each asset class.
    Falls back to hardcoded values if fetch fails.
    """
    import yfinance as yf

    real_stats = {}

    for asset in assets:
        symbols = ASSET_SYMBOLS.get(asset, [])
        if not symbols:
            real_stats[asset] = FALLBACK_RETURNS.get(asset, {"expected_return": 0.10, "volatility": 0.15})
            continue

        # Try each symbol until one works
        fetched = False
        for symbol in symbols[:2]:  # Try first 2 symbols
            try:
                ticker = yf.Ticker(symbol)
                df     = ticker.history(period=period)
                if df.empty or len(df) < 30:
                    continue

                returns       = df["Close"].pct_change().dropna()
                annual_return = float(returns.mean() * 252)
                annual_vol    = float(returns.std() * np.sqrt(252))

                if abs(annual_return) > 2.0 or annual_vol > 2.0:
                    continue

                real_stats[asset] = {
                    "expected_return": round(annual_return, 4),
                    "volatility":      round(annual_vol, 4),
                    "data_source":     "real",
                    "symbol":          symbol,
                    "data_points":     len(returns),
                }
                fetched = True
                logger.info(f"{asset}: return={annual_return:.2%}, vol={annual_vol:.2%}")
                break

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue

        if not fetched:
            fallback = FALLBACK_RETURNS.get(asset, {"expected_return": 0.10, "volatility": 0.15})
            real_stats[asset] = {**fallback, "data_source": "fallback"}

    return real_stats


def fetch_real_correlation_matrix(
    assets: List[str],
    period: str = "1y",
) -> np.ndarray:
    """
    Calculates real correlation matrix from historical data.
    """
    import yfinance as yf

    n         = len(assets)
    returns   = {}

    for asset in assets:
        symbols = ASSET_SYMBOLS.get(asset, [])
        if not symbols:
            continue
        try:
            ticker = yf.Ticker(symbols[0])
            df     = ticker.history(period=period)
            if not df.empty and len(df) > 30:
                ret = df["Close"].pct_change().dropna()
                returns[asset] = ret
        except Exception as e:
            logger.warning(f"Correlation fetch failed for {asset}: {e}")

    if len(returns) < 2:
        # Return default correlation matrix
        return _default_correlation_matrix(assets)

    # Align all series to same dates
    returns_df  = pd.DataFrame(returns).dropna()
    if len(returns_df) < 20:
        return _default_correlation_matrix(assets)

    corr_matrix = returns_df.corr()

    # Build full matrix including assets without data
    result = np.eye(n)
    for i, ai in enumerate(assets):
        for j, aj in enumerate(assets):
            if ai in corr_matrix.columns and aj in corr_matrix.columns:
                val = corr_matrix.loc[ai, aj] if ai != aj else 1.0
                if not np.isnan(val):
                    result[i][j] = float(val)
                else:
                    result[i][j] = _default_correlation(ai, aj)
            else:
                result[i][j] = _default_correlation(ai, aj)

    return result


def _default_correlation(asset_i: str, asset_j: str) -> float:
    """Default correlation based on asset class."""
    if asset_i == asset_j:
        return 1.0

    equity_assets = ["large_cap_equity", "mid_cap_equity", "small_cap_equity",
                     "index_funds", "international_funds", "hybrid_funds"]
    debt_assets   = ["debt_funds", "liquid_funds"]
    gold_assets   = ["gold_etf"]

    def get_class(a):
        if a in equity_assets:   return "equity"
        if a in debt_assets:     return "debt"
        if a in gold_assets:     return "gold"
        return "other"

    ci = get_class(asset_i)
    cj = get_class(asset_j)

    if ci == cj == "equity":   return 0.75
    if {ci, cj} == {"equity", "debt"}: return -0.20
    if {ci, cj} == {"equity", "gold"}: return 0.10
    if {ci, cj} == {"debt", "gold"}:   return 0.15
    return 0.30


def _default_correlation_matrix(assets: List[str]) -> np.ndarray:
    n      = len(assets)
    result = np.eye(n)
    for i in range(n):
        for j in range(n):
            if i != j:
                result[i][j] = _default_correlation(assets[i], assets[j])
    return result


def dynamic_mean_variance(
    assets: List[str],
    real_stats: Dict,
    corr_matrix: np.ndarray,
    risk_aversion: float = 2.0,
    news_signal: Dict = None,
) -> Dict:
    """
    Mean-Variance Optimization using REAL returns and correlations.
    Also incorporates news sentiment signal.
    """
    from scipy.optimize import minimize

    n       = len(assets)
    returns = np.array([real_stats[a]["expected_return"] for a in assets])
    vols    = np.array([real_stats[a]["volatility"] for a in assets])

    # News adjustment to returns
    if news_signal:
        sentiment   = news_signal.get("overall_news_score", 0)
        geo_risk    = news_signal.get("geo_risk", 0)
        equity_adj  = sentiment * 0.05 - geo_risk * 0.08

        equity_assets = ["large_cap_equity", "mid_cap_equity", "small_cap_equity",
                         "index_funds", "international_funds"]
        for i, asset in enumerate(assets):
            if asset in equity_assets:
                returns[i] *= (1 + equity_adj)

    # Covariance matrix from real correlations
    cov = np.outer(vols, vols) * corr_matrix

    def objective(weights):
        port_return = np.dot(weights, returns)
        port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        return -(port_return - risk_aversion * port_risk)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)
    result      = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights     = result.x

    port_return = float(np.dot(weights, returns))
    port_risk   = float(np.sqrt(np.dot(weights.T, np.dot(cov, weights))))
    sharpe      = (port_return - 0.06) / port_risk if port_risk > 0 else 0

    return {
        "method":          "Dynamic Mean-Variance (Real Data)",
        "allocation":      {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return": round(port_return * 100, 2),
        "expected_risk":   round(port_risk * 100, 2),
        "sharpe_ratio":    round(sharpe, 3),
        "data_source":     "real",
        "news_adjusted":   news_signal is not None,
    }


def dynamic_risk_parity(
    assets: List[str],
    real_stats: Dict,
    corr_matrix: np.ndarray,
) -> Dict:
    """Risk Parity with real covariance matrix."""
    from scipy.optimize import minimize

    n    = len(assets)
    vols = np.array([real_stats[a]["volatility"] for a in assets])
    cov  = np.outer(vols, vols) * corr_matrix

    def risk_parity_obj(weights):
        port_var      = np.dot(weights.T, np.dot(cov, weights))
        marginal_risk = np.dot(cov, weights)
        risk_contrib  = weights * marginal_risk / np.sqrt(port_var)
        target        = np.sqrt(port_var) / n
        return np.sum((risk_contrib - target) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)
    result      = minimize(risk_parity_obj, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights     = result.x

    returns     = np.array([real_stats[a]["expected_return"] for a in assets])
    port_return = float(np.dot(weights, returns))
    port_risk   = float(np.sqrt(np.dot(weights.T, np.dot(cov, weights))))
    sharpe      = (port_return - 0.06) / port_risk if port_risk > 0 else 0

    return {
        "method":          "Dynamic Risk Parity (Real Data)",
        "allocation":      {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return": round(port_return * 100, 2),
        "expected_risk":   round(port_risk * 100, 2),
        "sharpe_ratio":    round(sharpe, 3),
        "data_source":     "real",
    }


def get_dynamic_portfolio(
    assets: List[str],
    method: str = "markowitz",
    investment_amount: float = 1000000,
    news_signal: Dict = None,
    period: str = "2y",
) -> Dict:
    """
    Main function — builds portfolio using real data.
    Fetches real returns, real correlations, applies news signal.
    """
    logger.info(f"Building dynamic portfolio for {len(assets)} assets using real data...")

    # Fetch real stats
    real_stats   = fetch_real_asset_returns(assets, period=period)
    corr_matrix  = fetch_real_correlation_matrix(assets, period="1y")

    # Run optimization
    if method == "risk_parity":
        result = dynamic_risk_parity(assets, real_stats, corr_matrix)
    else:
        result = dynamic_mean_variance(assets, real_stats, corr_matrix, news_signal=news_signal)

    # Add rupee amounts
    result["investment_amount"] = investment_amount
    result["allocated_amounts"] = {
        asset: round(investment_amount * pct / 100, 2)
        for asset, pct in result["allocation"].items()
    }
    result["asset_stats"]       = real_stats
    result["calculated_at"]     = datetime.now().isoformat()

    # Data source summary
    real_count     = sum(1 for s in real_stats.values() if s.get("data_source") == "real")
    result["data_quality"] = {
        "real_data_assets":     real_count,
        "fallback_assets":      len(assets) - real_count,
        "total_assets":         len(assets),
        "real_data_percentage": round(real_count / len(assets) * 100, 1),
    }

    return result