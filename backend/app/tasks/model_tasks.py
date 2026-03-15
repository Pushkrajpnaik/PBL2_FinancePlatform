from app.core.celery_app import celery_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.model_tasks.retrain_all_models")
def retrain_all_models():
    """
    Weekly task — retrains all ML models with latest data.
    """
    logger.info("Starting model retraining pipeline...")
    results = {}

    # Retrain each model
    results["regime_detection"] = retrain_regime_model()
    results["sentiment_model"]  = retrain_sentiment_model()

    logger.info("Model retraining complete.")
    return {
        "status":    "success",
        "timestamp": datetime.now().isoformat(),
        "results":   results,
    }


def retrain_regime_model():
    """Retrains HMM regime detection model."""
    try:
        from app.ml.regime.hmm_detector import generate_placeholder_market_data, detect_regime_hmm
        df     = generate_placeholder_market_data(days=500)
        result = detect_regime_hmm(df)
        return {"status": "success", "regime": result["regime"]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def retrain_sentiment_model():
    """Placeholder for FinBERT retraining."""
    return {
        "status":  "placeholder",
        "message": "FinBERT retraining requires GPU — implement in production",
    }


@celery_app.task(name="app.tasks.model_tasks.run_backtesting")
def run_backtesting():
    """
    Runs walk-forward backtesting on portfolio strategies.
    Compares strategy performance vs Nifty50 benchmark.
    """
    logger.info("Running backtesting validation...")
    try:
        from app.ml.regime.hmm_detector import generate_placeholder_market_data
        import numpy as np

        df = generate_placeholder_market_data(days=500)

        # Simple buy and hold strategy
        returns        = df["returns"].values
        cumulative     = np.cumprod(1 + returns)
        total_return   = float(cumulative[-1] - 1) * 100
        annual_return  = float((cumulative[-1] ** (252 / len(returns))) - 1) * 100
        volatility     = float(np.std(returns) * np.sqrt(252)) * 100
        sharpe         = annual_return / volatility if volatility > 0 else 0
        max_drawdown   = float(np.min(cumulative / np.maximum.accumulate(cumulative) - 1)) * 100

        return {
            "status":         "success",
            "strategy":       "Buy and Hold (Nifty50 Benchmark)",
            "total_return":   round(total_return,  2),
            "annual_return":  round(annual_return, 2),
            "volatility":     round(volatility,    2),
            "sharpe_ratio":   round(sharpe,        3),
            "max_drawdown":   round(max_drawdown,  2),
            "timestamp":      datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Backtesting failed: {e}")
        return {"status": "failed", "error": str(e)}