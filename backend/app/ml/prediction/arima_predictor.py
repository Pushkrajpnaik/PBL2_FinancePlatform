import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


def run_adf_test(series: pd.Series) -> Dict:
    """
    Augmented Dickey-Fuller test for stationarity.
    Required before fitting ARIMA.
    """
    try:
        from statsmodels.tsa.stattools import adfuller
        result = adfuller(series.dropna())
        return {
            "adf_statistic": round(float(result[0]), 4),
            "p_value":       round(float(result[1]), 4),
            "is_stationary": bool(result[1] < 0.05),
            "critical_values": {k: round(v, 3) for k, v in result[4].items()},
        }
    except Exception as e:
        logger.error(f"ADF test failed: {e}")
        return {"is_stationary": False, "p_value": 1.0}


def fit_arima(
    series: pd.Series,
    order: Tuple = None,
) -> Optional[object]:
    """
    Fits ARIMA model to price series.
    Auto-selects order if not provided.
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA

        # Use returns (differenced series) for stationarity
        returns = series.pct_change().dropna()

        # Default order
        if order is None:
            order = (2, 0, 2)

        model  = ARIMA(returns, order=order)
        fitted = model.fit()
        logger.info(f"ARIMA{order} fitted. AIC: {fitted.aic:.2f}")
        return fitted

    except Exception as e:
        logger.error(f"ARIMA fitting failed: {e}")
        return None


def predict_arima(
    price_series: pd.Series,
    forecast_days: int = 30,
) -> Dict:
    """
    Predicts future prices using ARIMA on real price data.
    """
    try:
        if len(price_series) < 30:
            return {"error": "Insufficient data for ARIMA"}

        # Test stationarity on returns
        returns    = price_series.pct_change().dropna()
        adf_result = run_adf_test(returns)

        # Fit ARIMA
        fitted = fit_arima(price_series)
        if fitted is None:
            return {"error": "ARIMA fitting failed"}

        # Forecast returns
        forecast       = fitted.forecast(steps=forecast_days)
        forecast_ci    = fitted.get_forecast(steps=forecast_days).conf_int()

        # Convert returns forecast to price forecast
        last_price     = float(price_series.iloc[-1])
        predicted_prices = [last_price]

        for ret in forecast:
            next_price = predicted_prices[-1] * (1 + float(ret))
            predicted_prices.append(next_price)

        predicted_prices = predicted_prices[1:]  # Remove initial price

        # Generate date range
        last_date  = price_series.index[-1]
        if hasattr(last_date, "date"):
            last_date = last_date.date()
        future_dates = [
            (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
            for i in range(forecast_days)
        ]

        # Calculate confidence intervals for prices
        lower_bounds = []
        upper_bounds = []
        price        = last_price
        for i in range(forecast_days):
            lower_ret = float(forecast_ci.iloc[i, 0])
            upper_ret = float(forecast_ci.iloc[i, 1])
            lower_bounds.append(round(price * (1 + lower_ret), 2))
            upper_bounds.append(round(price * (1 + upper_ret), 2))
            price = predicted_prices[i]

        # Summary metrics
        final_predicted = predicted_prices[-1]
        expected_return = ((final_predicted / last_price) - 1) * 100
        direction       = "UP" if expected_return > 0 else "DOWN"

        return {
            "model":          "ARIMA",
            "current_price":  round(last_price, 2),
            "forecast_days":  forecast_days,
            "predictions": [
                {
                    "date":        future_dates[i],
                    "price":       round(predicted_prices[i], 2),
                    "lower_bound": lower_bounds[i],
                    "upper_bound": upper_bounds[i],
                }
                for i in range(forecast_days)
            ],
            "summary": {
                "predicted_price_30d": round(final_predicted, 2),
                "expected_return_30d": round(expected_return, 2),
                "direction":           direction,
                "confidence":          "Medium" if adf_result["is_stationary"] else "Low",
            },
            "stationarity": adf_result,
            "model_info": {
                "aic": round(float(fitted.aic), 2),
                "bic": round(float(fitted.bic), 2),
            },
        }

    except Exception as e:
        logger.error(f"ARIMA prediction failed: {e}")
        return {"error": str(e)}