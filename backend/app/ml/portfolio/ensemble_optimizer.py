import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regime-based weights for each method
# ---------------------------------------------------------------------------
REGIME_METHOD_WEIGHTS = {
    "Bull Market": {
        "markowitz":       0.40,
        "risk_parity":     0.20,
        "cvar":            0.10,
        "black_litterman": 0.30,
    },
    "Bear Market": {
        "markowitz":       0.15,
        "risk_parity":     0.35,
        "cvar":            0.40,
        "black_litterman": 0.10,
    },
    "High Volatility": {
        "markowitz":       0.10,
        "risk_parity":     0.30,
        "cvar":            0.50,
        "black_litterman": 0.10,
    },
    "Recovery": {
        "markowitz":       0.30,
        "risk_parity":     0.25,
        "cvar":            0.20,
        "black_litterman": 0.25,
    },
    "Sideways/Neutral": {
        "markowitz":       0.25,
        "risk_parity":     0.30,
        "cvar":            0.25,
        "black_litterman": 0.20,
    },
}


def combine_allocations(
    allocations: Dict[str, Dict[str, float]],
    weights:     Dict[str, float],
) -> Dict[str, float]:
    """
    Combines multiple portfolio allocations using weighted average.

    allocations = {
        "markowitz":   {"large_cap": 30, "debt": 20, ...},
        "risk_parity": {"large_cap": 25, "debt": 30, ...},
        ...
    }
    weights = {"markowitz": 0.4, "risk_parity": 0.3, ...}
    """
    all_assets = set()
    for alloc in allocations.values():
        all_assets.update(alloc.keys())

    combined = {}
    for asset in all_assets:
        weighted_sum = 0.0
        for method, alloc in allocations.items():
            method_weight = weights.get(method, 0)
            asset_weight  = alloc.get(asset, 0)
            weighted_sum += method_weight * asset_weight
        combined[asset] = round(weighted_sum, 2)

    # Normalize to ensure sum = 100%
    total = sum(combined.values())
    if total > 0:
        combined = {k: round(v / total * 100, 2) for k, v in combined.items()}

    return combined


def run_ensemble_optimization(
    assets:          List[str],
    risk_profile:    str = "Moderate",
    regime:          str = "Sideways/Neutral",
    news_signal:     Dict = None,
    investment_amount: float = 1000000,
    investor_views:  Dict = None,
) -> Dict:
    """
    Main ensemble optimizer — runs all 4 methods and combines them.
    Weights are determined by current market regime.
    """
    from app.ml.portfolio.optimizer import (
        mean_variance_optimization,
        risk_parity_optimization,
        cvar_optimization,
        black_litterman_optimization,
    )

    logger.info(f"Running ensemble optimization for {regime} regime...")

    # Step 1: Run all 4 methods
    results = {}
    errors  = {}

    try:
        results["markowitz"] = mean_variance_optimization(assets)
    except Exception as e:
        errors["markowitz"] = str(e)
        logger.error(f"Markowitz failed: {e}")

    try:
        results["risk_parity"] = risk_parity_optimization(assets)
    except Exception as e:
        errors["risk_parity"] = str(e)
        logger.error(f"Risk Parity failed: {e}")

    try:
        results["cvar"] = cvar_optimization(assets)
    except Exception as e:
        errors["cvar"] = str(e)
        logger.error(f"CVaR failed: {e}")

    try:
        results["black_litterman"] = black_litterman_optimization(
            assets, investor_views or {}
        )
    except Exception as e:
        errors["black_litterman"] = str(e)
        logger.error(f"Black-Litterman failed: {e}")

    if not results:
        return {"error": "All optimization methods failed"}

    # Step 2: Get regime-based weights
    base_weights = REGIME_METHOD_WEIGHTS.get(
        regime, REGIME_METHOD_WEIGHTS["Sideways/Neutral"]
    ).copy()

    # Step 3: Adjust weights based on news signal
    if news_signal:
        sentiment  = news_signal.get("overall_news_score", 0)
        geo_risk   = news_signal.get("geo_risk", 0)

        # High geo risk → increase CVaR weight (more protection)
        if geo_risk > 0.5:
            base_weights["cvar"]      = min(0.60, base_weights["cvar"] + 0.15)
            base_weights["markowitz"] = max(0.05, base_weights["markowitz"] - 0.10)
            base_weights["black_litterman"] = max(0.05, base_weights["black_litterman"] - 0.05)

        # Strong positive news → increase Markowitz weight (more return-seeking)
        elif sentiment > 0.3:
            base_weights["markowitz"]      = min(0.50, base_weights["markowitz"] + 0.10)
            base_weights["cvar"]           = max(0.05, base_weights["cvar"] - 0.10)

    # Normalize weights to sum to 1.0
    total_weight = sum(base_weights.values())
    weights = {k: round(v / total_weight, 4) for k, v in base_weights.items()}

    # Step 4: Only use weights for methods that succeeded
    active_weights = {k: v for k, v in weights.items() if k in results}
    total_active   = sum(active_weights.values())
    active_weights = {k: v / total_active for k, v in active_weights.items()}

    # Step 5: Combine allocations
    allocations = {method: res["allocation"] for method, res in results.items()}
    final_allocation = combine_allocations(allocations, active_weights)

    # Step 6: Calculate blended metrics
    blended_return = sum(
        active_weights.get(m, 0) * results[m].get("expected_return", 0)
        for m in results
    )
    blended_risk = sum(
        active_weights.get(m, 0) * results[m].get("expected_risk", 0)
        for m in results
    )
    blended_sharpe = (blended_return - 6) / blended_risk if blended_risk > 0 else 0

    # Step 7: Individual method comparison
    comparison = {}
    for method, res in results.items():
        comparison[method] = {
            "weight":          round(active_weights.get(method, 0) * 100, 1),
            "expected_return": res.get("expected_return", 0),
            "expected_risk":   res.get("expected_risk", 0),
            "sharpe_ratio":    res.get("sharpe_ratio", 0),
            "top_allocation":  max(res.get("allocation", {}).items(),
                                   key=lambda x: x[1], default=("N/A", 0)),
        }

    # Step 8: Explain why each weight was chosen
    explanations = _explain_weights(active_weights, regime, news_signal)

    return {
        "method":             "Ensemble (All 4 Combined)",
        "regime":             regime,
        "allocation":         final_allocation,
        "expected_return":    round(blended_return, 2),
        "expected_risk":      round(blended_risk, 2),
        "sharpe_ratio":       round(blended_sharpe, 3),
        "investment_amount":  investment_amount,
        "allocated_amounts": {
            asset: round(investment_amount * pct / 100, 2)
            for asset, pct in final_allocation.items()
        },
        "method_weights":     {k: round(v * 100, 1) for k, v in active_weights.items()},
        "method_comparison":  comparison,
        "weight_explanations": explanations,
        "news_adjusted":      news_signal is not None,
        "errors":             errors,
        "calculated_at":      datetime.now().isoformat(),
    }


def _explain_weights(
    weights: Dict[str, float],
    regime:  str,
    news_signal: Optional[Dict],
) -> Dict[str, str]:
    """Explains in plain English why each method got its weight."""
    explanations = {
        "markowitz": {
            "Bull Market":      "High weight — maximize returns in bull market",
            "Bear Market":      "Low weight — avoid aggressive return-chasing in bear market",
            "High Volatility":  "Very low weight — too risky in volatile market",
            "Recovery":         "Moderate weight — gradually increase return seeking",
            "Sideways/Neutral": "Moderate weight — balanced approach",
        },
        "risk_parity": {
            "Bull Market":      "Moderate weight — stability anchor",
            "Bear Market":      "High weight — equal risk distribution protects capital",
            "High Volatility":  "High weight — risk parity handles volatility best",
            "Recovery":         "Moderate weight — balanced risk distribution",
            "Sideways/Neutral": "High weight — best for uncertain conditions",
        },
        "cvar": {
            "Bull Market":      "Low weight — tail risk protection less needed",
            "Bear Market":      "Highest weight — protect against worst-case losses",
            "High Volatility":  "Highest weight — minimize extreme downside",
            "Recovery":         "Moderate weight — some protection still needed",
            "Sideways/Neutral": "Moderate weight — balanced protection",
        },
        "black_litterman": {
            "Bull Market":      "High weight — incorporate bullish market views",
            "Bear Market":      "Low weight — views unreliable in bear market",
            "High Volatility":  "Very low weight — views unreliable in volatility",
            "Recovery":         "Moderate weight — incorporate recovery views",
            "Sideways/Neutral": "Moderate weight — balanced view integration",
        },
    }

    result = {}
    for method, weight in weights.items():
        base_explanation = explanations.get(method, {}).get(regime, "Standard weight")
        news_note        = ""
        if news_signal:
            geo = news_signal.get("geo_risk", 0)
            if geo > 0.5 and method == "cvar":
                news_note = f" (boosted due to critical geo risk: {geo:.2f})"
            elif geo > 0.5 and method == "markowitz":
                news_note = f" (reduced due to critical geo risk: {geo:.2f})"
        result[method] = f"{base_explanation}{news_note} → Weight: {weight*100:.1f}%"

    return result