import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Placeholder market data (replace with real NSE/BSE data in later phases)
# ---------------------------------------------------------------------------
def generate_placeholder_market_data(days: int = 500) -> pd.DataFrame:
    """
    Generates realistic placeholder NIFTY50 price data.
    Replace this with real NSE data in the data ingestion phase.
    """
    np.random.seed(42)
    dates  = pd.date_range(end=datetime.today(), periods=days, freq="B")
    prices = [18000.0]

    for i in range(1, days):
        # Simulate different market regimes
        if i < 100:       # Bull market
            daily_return = np.random.normal(0.0008, 0.008)
        elif i < 200:     # Bear market
            daily_return = np.random.normal(-0.0005, 0.015)
        elif i < 300:     # High volatility
            daily_return = np.random.normal(0.0002, 0.025)
        elif i < 400:     # Recovery
            daily_return = np.random.normal(0.0006, 0.010)
        else:             # Normal
            daily_return = np.random.normal(0.0004, 0.010)

        prices.append(prices[-1] * (1 + daily_return))

    df = pd.DataFrame({"date": dates, "close": prices})
    df["returns"]    = df["close"].pct_change()
    df["volatility"] = df["returns"].rolling(20).std()
    df["momentum"]   = df["close"].pct_change(20)
    df = df.dropna()
    return df


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------
def extract_features(df: pd.DataFrame) -> np.ndarray:
    """
    Extract features for HMM regime detection.
    """
    features = np.column_stack([
        df["returns"].values,
        df["volatility"].values,
        df["momentum"].values,
    ])
    # Normalize
    mean = features.mean(axis=0)
    std  = features.std(axis=0)
    std[std == 0] = 1
    return (features - mean) / std


# ---------------------------------------------------------------------------
# Simple Regime Detection (Rule-Based as HMM fallback)
# ---------------------------------------------------------------------------
def detect_regime_rule_based(df: pd.DataFrame) -> Dict:
    """
    Rule-based market regime detection.
    Used as fallback if hmmlearn is not available.
    """
    latest = df.tail(20)

    avg_return     = latest["returns"].mean()
    avg_volatility = latest["volatility"].mean()
    momentum       = latest["momentum"].iloc[-1]

    # Classify regime
    if avg_return > 0.0005 and momentum > 0.03:
        regime       = "Bull Market"
        regime_id    = 0
        confidence   = min(95, 60 + abs(momentum) * 100)
        description  = "Strong upward trend with positive momentum. Equity markets are performing well."
        action       = "Increase equity exposure. Favor mid and small cap funds."
        color        = "green"
    elif avg_return < -0.0003 and momentum < -0.02:
        regime       = "Bear Market"
        regime_id    = 1
        confidence   = min(95, 60 + abs(momentum) * 100)
        description  = "Sustained downward trend with negative momentum. Markets under selling pressure."
        action       = "Rotate to defensive assets. Increase debt fund allocation. Reduce equity exposure."
        color        = "red"
    elif avg_volatility > 0.015:
        regime       = "High Volatility"
        regime_id    = 2
        confidence   = min(95, 60 + avg_volatility * 1000)
        description  = "Elevated market volatility with uncertain direction. High risk environment."
        action       = "Reduce overall risk. Increase cash and liquid fund positions."
        color        = "yellow"
    elif avg_return > 0.0002 and momentum > 0.0:
        regime       = "Recovery"
        regime_id    = 3
        confidence   = min(95, 55 + abs(momentum) * 50)
        description  = "Market stabilizing after a downturn. Early signs of recovery emerging."
        action       = "Gradually re-enter equities. Start SIP in large cap and index funds."
        color        = "blue"
    else:
        regime       = "Sideways/Neutral"
        regime_id    = 4
        confidence   = 60.0
        description  = "Market moving sideways with no clear trend. Low momentum environment."
        action       = "Maintain current allocation. Focus on systematic investing via SIP."
        color        = "gray"

    return {
        "regime":      regime,
        "regime_id":   regime_id,
        "confidence":  round(float(confidence), 2),
        "description": description,
        "action":      action,
        "color":       color,
    }


# ---------------------------------------------------------------------------
# HMM-Based Regime Detection
# ---------------------------------------------------------------------------
def detect_regime_hmm(df: pd.DataFrame) -> Dict:
    """
    HMM-based market regime detection using hmmlearn.
    Falls back to rule-based if hmmlearn unavailable.
    """
    try:
        from hmmlearn.hmm import GaussianHMM

        features = extract_features(df)

        model = GaussianHMM(
            n_components=4,
            covariance_type="full",
            n_iter=100,
            random_state=42,
        )
        model.fit(features)
        hidden_states = model.predict(features)

        # Analyze each state
        df_copy              = df.copy()
        df_copy["state"]     = hidden_states[-len(df_copy):]
        state_stats          = {}

        for state in range(4):
            state_data = df_copy[df_copy["state"] == state]
            if len(state_data) > 0:
                state_stats[state] = {
                    "mean_return":     state_data["returns"].mean(),
                    "mean_volatility": state_data["volatility"].mean(),
                    "count":           len(state_data),
                }

        # Map states to regimes based on return/volatility
        regime_map = {}
        for state, stats in state_stats.items():
            if stats["mean_return"] > 0.0005:
                regime_map[state] = "Bull Market"
            elif stats["mean_return"] < -0.0003:
                regime_map[state] = "Bear Market"
            elif stats["mean_volatility"] > 0.015:
                regime_map[state] = "High Volatility"
            else:
                regime_map[state] = "Recovery"

        current_state  = int(hidden_states[-1])
        current_regime = regime_map.get(current_state, "Sideways/Neutral")

        # Get transition probabilities
        trans_probs = model.transmat_[current_state]

        regime_details = {
            "Bull Market":    {"action": "Increase equity exposure",          "color": "green"},
            "Bear Market":    {"action": "Rotate to defensive assets",        "color": "red"},
            "High Volatility":{"action": "Reduce risk, increase cash",        "color": "yellow"},
            "Recovery":       {"action": "Gradually re-enter equities",       "color": "blue"},
            "Sideways/Neutral":{"action": "Maintain allocation, focus on SIP","color": "gray"},
        }

        details = regime_details.get(current_regime, regime_details["Sideways/Neutral"])

        return {
            "regime":               current_regime,
            "regime_id":            current_state,
            "confidence":           round(float(max(trans_probs)) * 100, 2),
            "description":          f"HMM detected {current_regime} with {len(state_stats)} distinct market states.",
            "action":               details["action"],
            "color":                details["color"],
            "detection_method":     "Hidden Markov Model",
            "transition_probabilities": {
                f"state_{i}": round(float(p), 3)
                for i, p in enumerate(trans_probs)
            },
        }

    except Exception as e:
        # Fallback to rule-based
        result = detect_regime_rule_based(df)
        result["detection_method"] = "Rule-Based (HMM fallback)"
        return result


# ---------------------------------------------------------------------------
# Portfolio adjustment based on regime
# ---------------------------------------------------------------------------
REGIME_ALLOCATION_ADJUSTMENTS = {
    "Bull Market": {
        "equity_multiplier": 1.20,
        "debt_multiplier":   0.80,
        "description":       "Overweight equities in bull market",
    },
    "Bear Market": {
        "equity_multiplier": 0.70,
        "debt_multiplier":   1.40,
        "description":       "Underweight equities, overweight debt in bear market",
    },
    "High Volatility": {
        "equity_multiplier": 0.80,
        "debt_multiplier":   1.20,
        "description":       "Reduce risk in high volatility regime",
    },
    "Recovery": {
        "equity_multiplier": 1.05,
        "debt_multiplier":   0.95,
        "description":       "Slightly overweight equities in recovery",
    },
    "Sideways/Neutral": {
        "equity_multiplier": 1.00,
        "debt_multiplier":   1.00,
        "description":       "Maintain neutral allocation in sideways market",
    },
}

def adjust_portfolio_for_regime(
    base_allocation: Dict[str, float],
    regime: str,
) -> Dict[str, float]:
    """
    Adjusts portfolio weights based on detected market regime.
    """
    adjustment = REGIME_ALLOCATION_ADJUSTMENTS.get(
        regime, REGIME_ALLOCATION_ADJUSTMENTS["Sideways/Neutral"]
    )

    equity_assets    = ["large_cap_equity", "mid_cap_equity", "small_cap_equity",
                        "index_funds", "international_funds"]
    debt_assets      = ["debt_funds", "liquid_funds", "hybrid_funds"]

    adjusted = {}
    for asset, weight in base_allocation.items():
        if asset in equity_assets:
            adjusted[asset] = weight * adjustment["equity_multiplier"]
        elif asset in debt_assets:
            adjusted[asset] = weight * adjustment["debt_multiplier"]
        else:
            adjusted[asset] = weight

    # Normalize to 100%
    total = sum(adjusted.values())
    adjusted = {k: round(v / total * 100, 2) for k, v in adjusted.items()}

    return adjusted