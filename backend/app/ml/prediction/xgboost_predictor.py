import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


def build_features(
    df: pd.DataFrame,
    news_sentiment_score: float = 0.0,
    macro_data: Dict = None,
) -> pd.DataFrame:
    """
    Builds feature matrix for XGBoost prediction.
    Includes technical indicators + news sentiment + macro data.
    """
    features = pd.DataFrame(index=df.index)

    # Price features
    features["returns"]          = df["close"].pct_change()
    features["returns_5d"]       = df["close"].pct_change(5)
    features["returns_20d"]      = df["close"].pct_change(20)
    features["volatility_20d"]   = features["returns"].rolling(20, min_periods=1).std()

    # Technical indicators
    features["sma_ratio"]        = df["close"] / df["close"].rolling(20, min_periods=1).mean()
    features["price_momentum"]   = df["close"].pct_change(10)

    # RSI
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss     = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs       = gain / loss.replace(0, np.nan)
    features["rsi"] = (100 - (100 / (1 + rs))).fillna(50)

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    features["macd"] = ema12 - ema26

    # Volume
    if "volume" in df.columns:
        vol_sma              = df["volume"].rolling(20, min_periods=1).mean()
        features["vol_ratio"] = (df["volume"] / vol_sma.replace(0, np.nan)).fillna(1)
    else:
        features["vol_ratio"] = 1.0

    # News sentiment (novel feature!)
    features["news_sentiment"] = news_sentiment_score

    # Macro features
    if macro_data:
        features["usd_inr"]    = macro_data.get("forex", {}).get("usd_inr", 83.5)
        features["crude_oil"]  = macro_data.get("commodities", {}).get("crude_oil_usd", 75)
        features["gold_price"] = macro_data.get("commodities", {}).get("gold_usd_oz", 2000)
    else:
        features["usd_inr"]    = 83.5
        features["crude_oil"]  = 75.0
        features["gold_price"] = 2000.0

    # Target: next day return direction (1=up, 0=down)
    features["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    return features.dropna()


def train_xgboost(
    df: pd.DataFrame,
    news_sentiment_score: float = 0.0,
    macro_data: Dict = None,
) -> Dict:
    """
    Trains XGBoost on real market data with news sentiment as feature.
    """
    try:
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        features_df = build_features(df, news_sentiment_score, macro_data)
        if len(features_df) < 50:
            return {"error": "Insufficient data for XGBoost"}

        feature_cols = [c for c in features_df.columns if c != "target"]
        X = features_df[feature_cols].values
        y = features_df["target"].values

        # Train/test split
        split    = int(len(X) * 0.8)
        X_train  = X[:split]
        y_train  = y[:split]
        X_test   = X[split:]
        y_test   = y[split:]

        # Train XGBoost
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            verbosity=0,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred   = model.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))

        # Feature importance with SHAP-style values
        importance     = model.feature_importances_
        feature_importance = {
            feature_cols[i]: round(float(importance[i]), 4)
            for i in range(len(feature_cols))
        }
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        # Predict next day
        latest_features = X[-1].reshape(1, -1)
        next_day_pred   = model.predict(latest_features)[0]
        next_day_prob   = model.predict_proba(latest_features)[0]

        direction   = "UP" if next_day_pred == 1 else "DOWN"
        confidence  = float(max(next_day_prob)) * 100

        return {
            "model":              "XGBoost",
            "accuracy":           round(accuracy * 100, 2),
            "next_day_direction": direction,
            "confidence":         round(confidence, 2),
            "up_probability":     round(float(next_day_prob[1]) * 100, 2),
            "down_probability":   round(float(next_day_prob[0]) * 100, 2),
            "feature_importance": feature_importance,
            "news_sentiment_impact": round(float(feature_importance.get("news_sentiment", 0)), 4),
            "top_features": list(feature_importance.keys())[:5],
            "training_samples": len(X_train),
            "test_samples":     len(X_test),
        }

    except Exception as e:
        logger.error(f"XGBoost training failed: {e}")
        return {"error": str(e)}