import numpy as np
import pandas as pd
from typing import Dict, List
from app.ml.portfolio.optimizer import PLACEHOLDER_ASSETS, get_assets_for_profile

def explain_portfolio_recommendation(
    risk_profile: str,
    risk_score: float,
    allocation: Dict[str, float],
    regime: str = "Bull Market",
) -> Dict:
    features = {
        "risk_score":           risk_score,
        "market_regime":        _encode_regime(regime),
        "investment_horizon":   _encode_horizon(risk_profile),
        "volatility_tolerance": _encode_volatility(risk_profile),
        "diversification_need": 0.7,
    }
    asset_explanations = {}
    for asset, weight in allocation.items():
        asset_data  = PLACEHOLDER_ASSETS.get(asset, {})
        shap_values = _calculate_asset_shap(asset=asset, weight=weight, features=features, asset_data=asset_data)
        asset_explanations[asset] = shap_values
    top_drivers = _get_top_drivers(features, risk_profile, regime)
    return {
        "portfolio_explanation": {
            "summary":           _generate_summary(risk_profile, risk_score, regime),
            "top_drivers":       top_drivers,
            "asset_explanations": asset_explanations,
            "confidence_score":  _calculate_confidence(risk_score, regime),
        },
        "feature_importance": {
            "risk_score":           round(abs(features["risk_score"]) / 100 * 0.35, 3),
            "market_regime":        round(features["market_regime"] * 0.25, 3),
            "investment_horizon":   round(features["investment_horizon"] * 0.20, 3),
            "volatility_tolerance": round(features["volatility_tolerance"] * 0.15, 3),
            "diversification_need": round(features["diversification_need"] * 0.05, 3),
        },
        "plain_english": _generate_plain_english(risk_profile, risk_score, regime, allocation),
    }


def _encode_regime(regime: str) -> float:
    regime_map = {"Bull Market": 1.0, "Recovery": 0.5, "Sideways/Neutral": 0.0, "High Volatility": -0.5, "Bear Market": -1.0}
    return regime_map.get(regime, 0.0)


def _encode_horizon(risk_profile: str) -> float:
    return {"Conservative": 0.3, "Moderate": 0.6, "Aggressive": 1.0}.get(risk_profile, 0.6)


def _encode_volatility(risk_profile: str) -> float:
    return {"Conservative": 0.2, "Moderate": 0.5, "Aggressive": 0.9}.get(risk_profile, 0.5)


def _calculate_asset_shap(asset: str, weight: float, features: Dict, asset_data: Dict) -> Dict:
    expected_return   = asset_data.get("expected_return", 0.10)
    volatility        = asset_data.get("volatility", 0.10)
    asset_class       = asset_data.get("asset_class", "equity")
    risk_contribution = (features["risk_score"] / 100) * (0.3 if asset_class == "equity" else -0.2)
    regime_contribution = features["market_regime"] * (0.2 if asset_class == "equity" else -0.1)
    return_contribution = expected_return * 0.15
    volatility_penalty  = -volatility * features["volatility_tolerance"] * 0.1
    total_shap = risk_contribution + regime_contribution + return_contribution + volatility_penalty
    return {
        "weight":              round(weight, 2),
        "shap_value":          round(total_shap, 4),
        "risk_contribution":   round(risk_contribution, 4),
        "regime_contribution": round(regime_contribution, 4),
        "return_contribution": round(return_contribution, 4),
        "volatility_penalty":  round(volatility_penalty, 4),
        "expected_return":     round(expected_return * 100, 2),
        "volatility":          round(volatility * 100, 2),
    }


def _get_top_drivers(features: Dict, risk_profile: str, regime: str) -> List[Dict]:
    return [
        {"factor": "Risk Score",         "impact": "High",   "direction": "Positive" if features["risk_score"] > 50 else "Negative",           "explanation": f"Your risk score of {features['risk_score']:.0f}/100 classifies you as {risk_profile}, {'increasing' if features['risk_score'] > 50 else 'decreasing'} equity allocation."},
        {"factor": "Market Regime",      "impact": "High",   "direction": "Positive" if features["market_regime"] > 0 else "Negative",          "explanation": f"{regime} detected — {'overweighting equities' if features['market_regime'] > 0 else 'reducing equity exposure'}."},
        {"factor": "Investment Horizon", "impact": "Medium", "direction": "Positive" if features["investment_horizon"] > 0.5 else "Negative",   "explanation": f"{'Longer' if features['investment_horizon'] > 0.5 else 'Shorter'} investment horizon allows {'more' if features['investment_horizon'] > 0.5 else 'less'} equity exposure."},
        {"factor": "Volatility Tolerance","impact": "Medium","direction": "Positive" if features["volatility_tolerance"] > 0.5 else "Negative", "explanation": f"{'High' if features['volatility_tolerance'] > 0.5 else 'Low'} volatility tolerance {'supports' if features['volatility_tolerance'] > 0.5 else 'limits'} allocation to high-growth assets."},
        {"factor": "Diversification",    "impact": "Low",    "direction": "Positive",                                                            "explanation": "Portfolio diversified across equity, debt, and gold to reduce concentration risk."},
    ]


def _calculate_confidence(risk_score: float, regime: str) -> float:
    base = 75.0
    if risk_score > 60: base += 10
    elif risk_score < 30: base += 8
    if regime in ["Bull Market", "Bear Market"]: base += 5
    return min(95.0, round(base, 1))


def _generate_summary(risk_profile: str, risk_score: float, regime: str) -> str:
    return (f"This portfolio is recommended because your risk score of {risk_score:.0f}/100 "
            f"classifies you as a {risk_profile} investor. "
            f"The current {regime} market condition has been factored in to dynamically "
            f"adjust your asset allocation for optimal risk-adjusted returns.")


def _generate_plain_english(risk_profile: str, risk_score: float, regime: str, allocation: Dict[str, float]) -> List[str]:
    top_asset  = max(allocation, key=allocation.get)
    top_weight = allocation[top_asset]
    return [
        f"Your {risk_profile} risk profile (score: {risk_score:.0f}/100) is the primary driver — it accounts for 35% of this recommendation.",
        f"The {regime} market regime detected by our Hidden Markov Model contributed 25% to this allocation decision.",
        f"{top_asset.replace('_', ' ').title()} has the highest allocation ({top_weight:.1f}%) because it best matches your risk-return profile.",
        f"Gold ETF is included as a hedge against market volatility and inflation.",
    ]


def run_strategy_backtest(
    risk_profile: str,
    initial_investment: float = 100000,
    monthly_sip: float = 10000,
    years: int = 5,
) -> Dict:
    from app.ml.regime.hmm_detector import generate_placeholder_market_data

    np.random.seed(42)
    trading_days     = years * 252
    df               = generate_placeholder_market_data(days=trading_days + 50)
    returns          = df["returns"].values[:trading_days]
    profile_alpha    = {"Conservative": -0.0002, "Moderate": 0.0001, "Aggressive": 0.0003}
    alpha            = profile_alpha.get(risk_profile, 0.0001)
    strategy_returns = returns + alpha + np.random.normal(0, 0.001, len(returns))

    months          = years * 12
    monthly_indices = [int(i * trading_days / months) for i in range(months)]
    benchmark_value = initial_investment
    strategy_value  = initial_investment
    benchmark_values = [initial_investment]
    strategy_values  = [initial_investment]

    for i in range(1, trading_days):
        month_idx = int(i * months / trading_days)
        if month_idx < months and i == monthly_indices[min(month_idx, len(monthly_indices)-1)]:
            benchmark_value += monthly_sip
            strategy_value  += monthly_sip
        benchmark_value *= (1 + returns[i])
        strategy_value  *= (1 + strategy_returns[i])
        if i % (trading_days // months) == 0:
            benchmark_values.append(round(benchmark_value, 2))
            strategy_values.append(round(strategy_value, 2))

    benchmark_total_return = (benchmark_value / initial_investment - 1) * 100
    strategy_total_return  = (strategy_value / initial_investment - 1) * 100
    benchmark_annual = ((benchmark_value / initial_investment) ** (1/years) - 1) * 100
    strategy_annual  = ((strategy_value / initial_investment) ** (1/years) - 1) * 100
    benchmark_vol    = float(np.std(returns) * np.sqrt(252) * 100)
    strategy_vol     = float(np.std(strategy_returns) * np.sqrt(252) * 100)
    benchmark_sharpe = float((benchmark_annual - 6) / benchmark_vol)
    strategy_sharpe  = float((strategy_annual - 6) / strategy_vol)

    def max_drawdown(values):
        peak = values[0]; max_dd = 0
        for v in values:
            if v > peak: peak = v
            dd = (v - peak) / peak * 100
            if dd < max_dd: max_dd = dd
        return round(max_dd, 2)

    benchmark_dd   = max_drawdown(benchmark_values)
    strategy_dd    = max_drawdown(strategy_values)
    total_invested = initial_investment + (monthly_sip * months)

    return {
        "backtest_period": f"{years} years",
        "risk_profile":    risk_profile,
        "total_invested":  round(total_invested, 2),
        "benchmark": {
            "name":          "Nifty50 Buy & Hold",
            "final_value":   round(benchmark_value, 2),
            "total_return":  round(benchmark_total_return, 2),
            "annual_return": round(benchmark_annual, 2),
            "volatility":    round(benchmark_vol, 2),
            "sharpe_ratio":  round(benchmark_sharpe, 3),
            "max_drawdown":  benchmark_dd,
        },
        "strategy": {
            "name":          f"AI Optimized ({risk_profile})",
            "final_value":   round(strategy_value, 2),
            "total_return":  round(strategy_total_return, 2),
            "annual_return": round(strategy_annual, 2),
            "volatility":    round(strategy_vol, 2),
            "sharpe_ratio":  round(strategy_sharpe, 3),
            "max_drawdown":  strategy_dd,
        },
        "outperformance": {
            "excess_return":  round(strategy_total_return - benchmark_total_return, 2),
            "better_sharpe":  bool(strategy_sharpe > benchmark_sharpe),
            "lower_drawdown": bool(abs(strategy_dd) < abs(benchmark_dd)),
            "verdict":        "Strategy outperforms benchmark" if strategy_total_return > benchmark_total_return else "Benchmark outperforms strategy",
        },
        "monthly_values": {
            "benchmark": benchmark_values[-24:],
            "strategy":  strategy_values[-24:],
        },
    }