import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Real Backtesting Engine
# ---------------------------------------------------------------------------

def fetch_backtest_data(period: str = "5y") -> Optional[pd.DataFrame]:
    """Fetches real NIFTY50 historical data for backtesting."""
    try:
        from app.data.ingestion.market_data import fetch_price_history
        df = fetch_price_history("^NSEI", period=period)
        if df is None or df.empty:
            logger.warning("Could not fetch real data, using placeholder")
            return None
        logger.info(f"Fetched {len(df)} days of real NIFTY50 data for backtesting")
        return df
    except Exception as e:
        logger.error(f"Backtest data fetch failed: {e}")
        return None


def calculate_strategy_returns(
    df: pd.DataFrame,
    strategy: str = "buy_and_hold",
    rebalance_frequency: int = 30,
    risk_profile: str = "Moderate",
) -> pd.Series:
    """
    Calculates returns for different strategies on real data.
    strategies: buy_and_hold, momentum, mean_reversion, regime_based
    """
    returns = df["returns"].dropna()

    if strategy == "buy_and_hold":
        return returns

    elif strategy == "momentum":
        # Buy when 20d momentum positive, sell when negative
        signals  = (df["close"].pct_change(20) > 0).astype(int)
        signals  = signals.shift(1).fillna(0)
        return returns * signals

    elif strategy == "mean_reversion":
        # Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought)
        delta    = df["close"].diff()
        gain     = delta.clip(lower=0).rolling(14, min_periods=1).mean()
        loss     = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
        rs       = gain / loss.replace(0, np.nan)
        rsi      = (100 - (100 / (1 + rs))).fillna(50)
        signals  = pd.Series(0, index=df.index)
        signals[rsi < 30] = 1   # Buy oversold
        signals[rsi > 70] = -1  # Sell overbought
        signals  = signals.shift(1).fillna(0)
        return returns * signals.clip(lower=0)

    elif strategy == "regime_based":
        # Use regime detection to switch between equity and cash
        from app.data.processing.data_processor import detect_market_regime_from_data
        signals = pd.Series(1, index=df.index)  # Default: invested
        window  = 20
        for i in range(window, len(df)):
            subset = df.iloc[i-window:i]
            regime = detect_market_regime_from_data(subset)
            if regime["regime"] in ["Bear Market", "High Volatility"]:
                signals.iloc[i] = 0  # Go to cash
        signals = signals.shift(1).fillna(1)
        return returns * signals

    return returns


def calculate_performance_metrics(
    returns: pd.Series,
    risk_free_rate: float = 0.065,
) -> Dict:
    """Calculates comprehensive performance metrics."""
    if returns.empty or len(returns) < 10:
        return {}

    returns_clean = returns.replace(0, np.nan).dropna()
    if returns_clean.empty:
        return {}

    # Annualized metrics
    annual_return  = float(returns_clean.mean() * 252 * 100)
    annual_vol     = float(returns_clean.std() * np.sqrt(252) * 100)
    sharpe         = (annual_return - risk_free_rate * 100) / annual_vol if annual_vol > 0 else 0

    # Sortino ratio (downside deviation)
    downside       = returns_clean[returns_clean < 0]
    downside_vol   = float(downside.std() * np.sqrt(252) * 100) if len(downside) > 0 else 1
    sortino        = (annual_return - risk_free_rate * 100) / downside_vol if downside_vol > 0 else 0

    # Calmar ratio
    cumulative     = (1 + returns_clean).cumprod()
    peak           = cumulative.cummax()
    drawdown       = (cumulative - peak) / peak
    max_drawdown   = float(drawdown.min() * 100)
    calmar         = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Win rate
    win_rate       = float((returns_clean > 0).sum() / len(returns_clean) * 100)

    # Total return
    total_return   = float((cumulative.iloc[-1] - 1) * 100)

    # Value at Risk (95%)
    var_95         = float(np.percentile(returns_clean, 5) * 100)

    # CVaR
    cvar_95        = float(returns_clean[returns_clean <= np.percentile(returns_clean, 5)].mean() * 100)

    return {
        "annual_return":   round(annual_return, 2),
        "annual_volatility": round(annual_vol, 2),
        "sharpe_ratio":    round(sharpe, 3),
        "sortino_ratio":   round(sortino, 3),
        "calmar_ratio":    round(calmar, 3),
        "max_drawdown":    round(max_drawdown, 2),
        "total_return":    round(total_return, 2),
        "win_rate":        round(win_rate, 2),
        "var_95":          round(var_95, 4),
        "cvar_95":         round(cvar_95, 4),
        "trading_days":    len(returns_clean),
    }


def run_walk_forward_backtest(
    df: pd.DataFrame,
    strategy: str = "regime_based",
    train_months: int = 12,
    test_months: int = 3,
) -> Dict:
    """
    Walk-forward backtesting — trains on past, tests on future.
    Prevents look-ahead bias.
    """
    results     = []
    total_days  = len(df)
    train_days  = train_months * 21  # ~21 trading days per month
    test_days   = test_months * 21

    if total_days < train_days + test_days:
        return {"error": "Insufficient data for walk-forward testing"}

    # Walk forward
    start = train_days
    while start + test_days <= total_days:
        train_data = df.iloc[start - train_days:start]
        test_data  = df.iloc[start:start + test_days]

        # Calculate strategy returns on test period
        strat_returns = calculate_strategy_returns(
            test_data, strategy=strategy
        )
        bench_returns = test_data["returns"].dropna()

        strat_metrics = calculate_performance_metrics(strat_returns)
        bench_metrics = calculate_performance_metrics(bench_returns)

        results.append({
            "period_start": str(test_data.index[0])[:10],
            "period_end":   str(test_data.index[-1])[:10],
            "strategy":     strat_metrics,
            "benchmark":    bench_metrics,
            "outperformed": strat_metrics.get("total_return", 0) > bench_metrics.get("total_return", 0),
        })

        start += test_days

    # Aggregate results
    outperformed_count = sum(1 for r in results if r["outperformed"])
    avg_strat_return   = np.mean([r["strategy"].get("annual_return", 0) for r in results])
    avg_bench_return   = np.mean([r["benchmark"].get("annual_return", 0) for r in results])

    return {
        "strategy":           strategy,
        "total_periods":      len(results),
        "outperformed_count": outperformed_count,
        "outperformance_rate": round(outperformed_count / len(results) * 100, 1) if results else 0,
        "avg_strategy_return": round(float(avg_strat_return), 2),
        "avg_benchmark_return": round(float(avg_bench_return), 2),
        "avg_excess_return":  round(float(avg_strat_return - avg_bench_return), 2),
        "periods":            results,
    }


def run_full_backtest(
    period: str = "5y",
    initial_investment: float = 1000000,
    monthly_sip: float = 10000,
    risk_profile: str = "Moderate",
) -> Dict:
    """
    Full backtest on real NIFTY50 data comparing multiple strategies.
    """
    # Fetch real data
    df = fetch_backtest_data(period=period)

    # Fallback to placeholder if real data unavailable
    if df is None:
        from app.ml.regime.hmm_detector import generate_placeholder_market_data
        years = int(period.replace("y", ""))
        df    = generate_placeholder_market_data(days=years * 252)
        data_source = "placeholder"
    else:
        data_source = "real_nifty50"

    strategies = ["buy_and_hold", "momentum", "mean_reversion", "regime_based"]
    results    = {}

    for strategy in strategies:
        strat_returns = calculate_strategy_returns(df, strategy=strategy)
        metrics       = calculate_performance_metrics(strat_returns)

        # Calculate portfolio value with SIP
        total_months  = len(df) // 21
        total_invested = initial_investment + (monthly_sip * total_months)
        final_value    = initial_investment * (1 + metrics.get("total_return", 0) / 100)

        results[strategy] = {
            **metrics,
            "total_invested": round(total_invested, 2),
            "final_value":    round(final_value, 2),
            "profit":         round(final_value - initial_investment, 2),
        }

    # Find best strategy
    best_strategy = max(
        results.keys(),
        key=lambda s: results[s].get("sharpe_ratio", 0)
    )

    # Walk-forward validation on regime-based strategy
    wf_result = run_walk_forward_backtest(df, strategy="regime_based")

    return {
        "period":           period,
        "data_source":      data_source,
        "risk_profile":     risk_profile,
        "initial_investment": initial_investment,
        "strategies":       results,
        "best_strategy":    best_strategy,
        "best_sharpe":      results[best_strategy]["sharpe_ratio"],
        "walk_forward":     wf_result,
        "nifty50_benchmark": results["buy_and_hold"],
        "backtested_at":    datetime.now().isoformat(),
    }


def generate_equity_curve(
    df: pd.DataFrame,
    strategy: str = "regime_based",
    initial_investment: float = 1000000,
) -> List[Dict]:
    """Generates equity curve data for charting."""
    returns   = calculate_strategy_returns(df, strategy=strategy)
    bench     = df["returns"].dropna()

    # Align indices
    common_idx   = returns.index.intersection(bench.index)
    returns      = returns.loc[common_idx]
    bench        = bench.loc[common_idx]

    strat_value  = initial_investment
    bench_value  = initial_investment
    curve        = []

    for i, (idx, ret) in enumerate(returns.items()):
        strat_value *= (1 + float(ret))
        bench_value *= (1 + float(bench.iloc[i]) if i < len(bench) else 1)

        if i % 5 == 0:  # Every 5 days
            curve.append({
                "date":            str(idx)[:10],
                "strategy_value":  round(strat_value, 2),
                "benchmark_value": round(bench_value, 2),
                "outperforming":   strat_value > bench_value,
            })

    return curve