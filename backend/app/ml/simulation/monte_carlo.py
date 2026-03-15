import numpy as np
from typing import Dict, List

def run_monte_carlo(
    initial_investment: float,
    monthly_sip: float,
    expected_annual_return: float,
    annual_volatility: float,
    time_horizon_years: int,
    num_simulations: int = 10000,
) -> Dict:
    """
    Runs Monte Carlo simulation for portfolio growth.
    Returns full probability distribution and risk metrics.
    """
    np.random.seed(42)

    # Convert annual to monthly
    monthly_return = expected_annual_return / 12
    monthly_volatility = annual_volatility / np.sqrt(12)
    total_months = time_horizon_years * 12

    # Store final portfolio values
    final_values = np.zeros(num_simulations)

    for i in range(num_simulations):
        portfolio_value = initial_investment
        for month in range(total_months):
            # Random monthly return from normal distribution
            random_return = np.random.normal(monthly_return, monthly_volatility)
            portfolio_value = portfolio_value * (1 + random_return) + monthly_sip
        final_values[i] = portfolio_value

    # Sort for percentile calculations
    final_values.sort()

    # Calculate key metrics
    percentile_5  = float(np.percentile(final_values, 5))
    percentile_25 = float(np.percentile(final_values, 25))
    percentile_50 = float(np.percentile(final_values, 50))
    percentile_75 = float(np.percentile(final_values, 75))
    percentile_95 = float(np.percentile(final_values, 95))

    # Total invested amount
    total_invested = initial_investment + (monthly_sip * total_months)

    # VaR — maximum expected loss at 95% confidence
    var_95 = float(total_invested - percentile_5)

    # CVaR — expected loss in worst 5% of scenarios
    worst_5_percent = final_values[:int(num_simulations * 0.05)]
    cvar_95 = float(total_invested - np.mean(worst_5_percent))

    # Probability of profit
    prob_profit = float(np.sum(final_values > total_invested) / num_simulations * 100)

    # Probability of doubling
    prob_double = float(np.sum(final_values > total_invested * 2) / num_simulations * 100)

    return {
        "num_simulations":    num_simulations,
        "time_horizon_years": time_horizon_years,
        "initial_investment": initial_investment,
        "monthly_sip":        monthly_sip,
        "total_invested":     round(total_invested, 2),
        "scenarios": {
            "worst_case":    round(percentile_5,  2),
            "below_average": round(percentile_25, 2),
            "median":        round(percentile_50, 2),
            "above_average": round(percentile_75, 2),
            "best_case":     round(percentile_95, 2),
        },
        "risk_metrics": {
            "value_at_risk_95":       round(var_95,  2),
            "conditional_var_95":     round(cvar_95, 2),
            "probability_of_profit":  round(prob_profit, 2),
            "probability_of_doubling": round(prob_double, 2),
        },
        "expected_return_multiple": round(percentile_50 / total_invested, 2),
    }


def calculate_goal_success_probability(
    initial_investment: float,
    monthly_sip: float,
    expected_annual_return: float,
    annual_volatility: float,
    time_horizon_years: int,
    target_amount: float,
    num_simulations: int = 10000,
) -> Dict:
    """
    Calculates probability of reaching a specific financial goal.
    """
    np.random.seed(42)

    monthly_return     = expected_annual_return / 12
    monthly_volatility = annual_volatility / np.sqrt(12)
    total_months       = time_horizon_years * 12

    final_values = np.zeros(num_simulations)

    for i in range(num_simulations):
        portfolio_value = initial_investment
        for month in range(total_months):
            random_return = np.random.normal(monthly_return, monthly_volatility)
            portfolio_value = portfolio_value * (1 + random_return) + monthly_sip
        final_values[i] = portfolio_value

    success_count = np.sum(final_values >= target_amount)
    success_probability = float(success_count / num_simulations * 100)

    return {
        "target_amount":        target_amount,
        "success_probability":  round(success_probability, 2),
        "median_outcome":       round(float(np.percentile(final_values, 50)), 2),
        "worst_case":           round(float(np.percentile(final_values, 5)),  2),
        "best_case":            round(float(np.percentile(final_values, 95)), 2),
        "shortfall_risk":       round(100 - success_probability, 2),
    }


# Risk profile return assumptions
RISK_PROFILE_ASSUMPTIONS = {
    "Conservative": {
        "expected_annual_return": 0.08,
        "annual_volatility":      0.05,
    },
    "Moderate": {
        "expected_annual_return": 0.12,
        "annual_volatility":      0.10,
    },
    "Aggressive": {
        "expected_annual_return": 0.15,
        "annual_volatility":      0.18,
    },
}