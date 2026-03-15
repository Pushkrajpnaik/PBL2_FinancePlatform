import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Placeholder asset data (replace with real data in later phases)
# ---------------------------------------------------------------------------
PLACEHOLDER_ASSETS = {
    "large_cap_equity": {
        "expected_return": 0.14,
        "volatility":      0.18,
        "asset_class":     "equity",
    },
    "mid_cap_equity": {
        "expected_return": 0.16,
        "volatility":      0.22,
        "asset_class":     "equity",
    },
    "small_cap_equity": {
        "expected_return": 0.18,
        "volatility":      0.28,
        "asset_class":     "equity",
    },
    "index_funds": {
        "expected_return": 0.13,
        "volatility":      0.16,
        "asset_class":     "equity",
    },
    "international_funds": {
        "expected_return": 0.12,
        "volatility":      0.20,
        "asset_class":     "equity",
    },
    "debt_funds": {
        "expected_return": 0.07,
        "volatility":      0.04,
        "asset_class":     "debt",
    },
    "hybrid_funds": {
        "expected_return": 0.10,
        "volatility":      0.10,
        "asset_class":     "hybrid",
    },
    "liquid_funds": {
        "expected_return": 0.06,
        "volatility":      0.01,
        "asset_class":     "debt",
    },
    "gold_etf": {
        "expected_return": 0.09,
        "volatility":      0.15,
        "asset_class":     "commodity",
    },
}

# Correlation matrix placeholder
def get_correlation_matrix(assets: List[str]) -> np.ndarray:
    n = len(assets)
    corr = np.eye(n)
    for i in range(n):
        for j in range(n):
            if i == j:
                corr[i][j] = 1.0
            else:
                ai = PLACEHOLDER_ASSETS[assets[i]]["asset_class"]
                aj = PLACEHOLDER_ASSETS[assets[j]]["asset_class"]
                if ai == aj:
                    corr[i][j] = 0.75
                elif {ai, aj} == {"equity", "debt"}:
                    corr[i][j] = -0.20
                elif {ai, aj} == {"equity", "commodity"}:
                    corr[i][j] = 0.10
                else:
                    corr[i][j] = 0.30
    return corr

def get_covariance_matrix(assets: List[str]) -> np.ndarray:
    vols = np.array([PLACEHOLDER_ASSETS[a]["volatility"] for a in assets])
    corr = get_correlation_matrix(assets)
    cov  = np.outer(vols, vols) * corr
    return cov

# ---------------------------------------------------------------------------
# 1. Mean-Variance Optimization (Markowitz)
# ---------------------------------------------------------------------------
def mean_variance_optimization(
    assets: List[str],
    risk_aversion: float = 2.0,
) -> Dict:
    n       = len(assets)
    returns = np.array([PLACEHOLDER_ASSETS[a]["expected_return"] for a in assets])
    cov     = get_covariance_matrix(assets)

    def objective(weights):
        port_return = np.dot(weights, returns)
        port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        return -(port_return - risk_aversion * port_risk)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)

    result  = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x

    port_return = np.dot(weights, returns)
    port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    sharpe      = (port_return - 0.06) / port_risk

    return {
        "method":            "Mean-Variance Optimization (Markowitz)",
        "allocation":        {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return":   round(float(port_return) * 100, 2),
        "expected_risk":     round(float(port_risk) * 100, 2),
        "sharpe_ratio":      round(float(sharpe), 3),
    }

# ---------------------------------------------------------------------------
# 2. Risk Parity
# ---------------------------------------------------------------------------
def risk_parity_optimization(assets: List[str]) -> Dict:
    n   = len(assets)
    cov = get_covariance_matrix(assets)

    def risk_parity_objective(weights):
        port_var = np.dot(weights.T, np.dot(cov, weights))
        marginal_risk = np.dot(cov, weights)
        risk_contrib  = weights * marginal_risk / np.sqrt(port_var)
        target = np.sqrt(port_var) / n
        return np.sum((risk_contrib - target) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)

    result  = minimize(risk_parity_objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x

    returns     = np.array([PLACEHOLDER_ASSETS[a]["expected_return"] for a in assets])
    port_return = np.dot(weights, returns)
    port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    sharpe      = (port_return - 0.06) / port_risk

    return {
        "method":          "Risk Parity",
        "allocation":      {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return": round(float(port_return) * 100, 2),
        "expected_risk":   round(float(port_risk) * 100, 2),
        "sharpe_ratio":    round(float(sharpe), 3),
    }

# ---------------------------------------------------------------------------
# 3. CVaR Optimization
# ---------------------------------------------------------------------------
def cvar_optimization(
    assets: List[str],
    confidence_level: float = 0.95,
    num_scenarios: int = 10000,
) -> Dict:
    n       = len(assets)
    returns = np.array([PLACEHOLDER_ASSETS[a]["expected_return"] for a in assets])
    cov     = get_covariance_matrix(assets)

    # Generate scenarios
    np.random.seed(42)
    scenarios = np.random.multivariate_normal(
        returns / 12,
        cov / 12,
        num_scenarios,
    )

    def cvar_objective(weights):
        port_returns = scenarios @ weights
        var_threshold = np.percentile(port_returns, (1 - confidence_level) * 100)
        cvar = -np.mean(port_returns[port_returns <= var_threshold])
        return cvar

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)

    result  = minimize(cvar_objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x

    port_return = np.dot(weights, returns)
    port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    sharpe      = (port_return - 0.06) / port_risk

    return {
        "method":          "CVaR Optimization",
        "allocation":      {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return": round(float(port_return) * 100, 2),
        "expected_risk":   round(float(port_risk) * 100, 2),
        "sharpe_ratio":    round(float(sharpe), 3),
    }

# ---------------------------------------------------------------------------
# 4. Black-Litterman
# ---------------------------------------------------------------------------
def black_litterman_optimization(
    assets: List[str],
    investor_views: Dict[str, float] = None,
) -> Dict:
    n       = len(assets)
    returns = np.array([PLACEHOLDER_ASSETS[a]["expected_return"] for a in assets])
    cov     = get_covariance_matrix(assets)

    # Market equilibrium weights (equal weight as placeholder)
    market_weights = np.array([1.0 / n] * n)
    risk_aversion  = 2.5
    tau            = 0.05

    # Equilibrium returns
    pi = risk_aversion * np.dot(cov, market_weights)

    # Apply investor views if provided
    if investor_views:
        view_assets  = [a for a in investor_views if a in assets]
        view_returns = np.array([investor_views[a] for a in view_assets])
        P = np.zeros((len(view_assets), n))
        for i, asset in enumerate(view_assets):
            P[i, assets.index(asset)] = 1.0
        omega  = np.diag(np.diag(tau * P @ cov @ P.T))
        M_inv  = np.linalg.inv(np.linalg.inv(tau * cov) + P.T @ np.linalg.inv(omega) @ P)
        bl_returns = M_inv @ (np.linalg.inv(tau * cov) @ pi + P.T @ np.linalg.inv(omega) @ view_returns)
    else:
        bl_returns = pi + returns * 0.1

    # Optimize with BL returns
    def objective(weights):
        port_return = np.dot(weights, bl_returns)
        port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        return -(port_return - risk_aversion * port_risk)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.02, 0.50) for _ in range(n)]
    w0          = np.array([1.0 / n] * n)

    result  = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x

    port_return = np.dot(weights, returns)
    port_risk   = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    sharpe      = (port_return - 0.06) / port_risk

    return {
        "method":          "Black-Litterman",
        "allocation":      {assets[i]: round(float(weights[i]) * 100, 2) for i in range(n)},
        "expected_return": round(float(port_return) * 100, 2),
        "expected_risk":   round(float(port_risk) * 100, 2),
        "sharpe_ratio":    round(float(sharpe), 3),
    }

# ---------------------------------------------------------------------------
# Get assets by risk profile
# ---------------------------------------------------------------------------
def get_assets_for_profile(risk_profile: str) -> List[str]:
    if risk_profile == "Conservative":
        return ["debt_funds", "liquid_funds", "large_cap_equity", "gold_etf", "index_funds"]
    elif risk_profile == "Moderate":
        return ["large_cap_equity", "index_funds", "hybrid_funds", "debt_funds", "gold_etf"]
    else:  # Aggressive
        return ["large_cap_equity", "mid_cap_equity", "small_cap_equity", "index_funds", "international_funds", "gold_etf", "debt_funds"]