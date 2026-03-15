import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# News-Driven Prediction Engine
# ---------------------------------------------------------------------------

def get_live_news_sentiment() -> Dict:
    """
    Fetches latest news sentiment from cache or live.
    Returns sentiment scores for use in predictions.
    """
    try:
        from app.data.processing.cache_manager import get_cached_news_sentiment
        from app.data.ingestion.news_fetcher import fetch_all_news
        from app.ml.nlp.news_analyzer import analyze_all_news

        # Try cache first
        cached = get_cached_news_sentiment()
        if cached:
            return cached

        # Fetch fresh
        articles = fetch_all_news(max_per_feed=8)
        if articles:
            result = analyze_all_news(articles, use_finbert=True)
            from app.data.processing.cache_manager import cache_news_sentiment
            cache_news_sentiment(result)
            return result

        return {}
    except Exception as e:
        logger.error(f"Failed to get news sentiment: {e}")
        return {}


def calculate_news_features(news_data: Dict) -> Dict:
    """
    Converts news sentiment data into ML features.
    """
    if not news_data:
        return {
            "overall_sentiment":    0.0,
            "banking_sentiment":    0.0,
            "it_sentiment":         0.0,
            "energy_sentiment":     0.0,
            "fmcg_sentiment":       0.0,
            "auto_sentiment":       0.0,
            "geo_risk_score":       0.0,
            "risk_alert_count":     0,
            "bullish_article_pct":  0.5,
            "bearish_article_pct":  0.5,
        }

    sector_sentiment = news_data.get("sector_sentiment", {})
    articles         = news_data.get("articles", [])

    # Count bullish/bearish articles
    total    = len(articles) if articles else 1
    bullish  = sum(1 for a in articles if a.get("sentiment") == "Positive")
    bearish  = sum(1 for a in articles if a.get("sentiment") == "Negative")

    return {
        "overall_sentiment":   float(news_data.get("overall_score", 0)),
        "banking_sentiment":   float(sector_sentiment.get("banking", {}).get("avg_score", 0) if isinstance(sector_sentiment.get("banking"), dict) else 0),
        "it_sentiment":        float(sector_sentiment.get("it", {}).get("avg_score", 0) if isinstance(sector_sentiment.get("it"), dict) else 0),
        "energy_sentiment":    float(sector_sentiment.get("energy", {}).get("avg_score", 0) if isinstance(sector_sentiment.get("energy"), dict) else 0),
        "fmcg_sentiment":      float(sector_sentiment.get("fmcg", {}).get("avg_score", 0) if isinstance(sector_sentiment.get("fmcg"), dict) else 0),
        "auto_sentiment":      float(sector_sentiment.get("auto", {}).get("avg_score", 0) if isinstance(sector_sentiment.get("auto"), dict) else 0),
        "geo_risk_score":      float(news_data.get("geopolitical_risk", {}).get("max_score", 0) if isinstance(news_data.get("geopolitical_risk"), dict) else 0),
        "risk_alert_count":    int(news_data.get("total_risk_alerts", 0)),
        "bullish_article_pct": round(bullish / total, 3),
        "bearish_article_pct": round(bearish / total, 3),
    }


def news_adjusted_arima_prediction(
    price_series: pd.Series,
    news_data: Dict,
    forecast_days: int = 30,
) -> Dict:
    """
    ARIMA prediction adjusted by news sentiment.
    News acts as a bias adjustment on the forecast.
    """
    from app.ml.prediction.arima_predictor import predict_arima

    # Base ARIMA prediction
    base_result = predict_arima(price_series, forecast_days=forecast_days)
    if "error" in base_result:
        return base_result

    # News features
    news_features  = calculate_news_features(news_data)
    sentiment_score = news_features["overall_sentiment"]
    geo_risk        = news_features["geo_risk_score"]

    # Calculate news adjustment
    # Positive news → boost predictions slightly
    # Negative news + high geo risk → reduce predictions
    news_adjustment = sentiment_score * 0.02 - geo_risk * 0.03

    # Apply adjustment to predictions
    adjusted_predictions = []
    for pred in base_result["predictions"]:
        adj_price = pred["price"] * (1 + news_adjustment)
        adjusted_predictions.append({
            **pred,
            "price":       round(adj_price, 2),
            "lower_bound": round(pred["lower_bound"] * (1 + news_adjustment - 0.01), 2),
            "upper_bound": round(pred["upper_bound"] * (1 + news_adjustment + 0.01), 2),
            "news_adjusted": True,
        })

    # Update summary
    final_price     = adjusted_predictions[-1]["price"]
    current_price   = base_result["current_price"]
    expected_return = ((final_price / current_price) - 1) * 100

    return {
        **base_result,
        "predictions": adjusted_predictions,
        "news_adjustment": {
            "sentiment_score":  round(sentiment_score, 4),
            "geo_risk_score":   round(geo_risk, 4),
            "price_adjustment": round(news_adjustment * 100, 4),
            "impact":           "Negative" if news_adjustment < 0 else "Positive",
        },
        "summary": {
            **base_result["summary"],
            "predicted_price_30d":   round(final_price, 2),
            "expected_return_30d":   round(expected_return, 2),
            "direction":             "UP" if expected_return > 0 else "DOWN",
            "news_adjusted":         True,
        },
        "model": "ARIMA + News Sentiment",
    }


def news_driven_xgboost_prediction(
    df: pd.DataFrame,
    news_data: Dict,
    macro_data: Dict = None,
) -> Dict:
    """
    XGBoost prediction with full news feature integration.
    Uses sector sentiment, geo risk, and article counts as features.
    """
    try:
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        import shap

        news_features = calculate_news_features(news_data)

        # Build enhanced feature matrix
        features = _build_enhanced_features(df, news_features, macro_data)
        if len(features) < 50:
            return {"error": "Insufficient data"}

        feature_cols = [c for c in features.columns if c != "target"]
        X = features[feature_cols].values
        y = features["target"].values

        split   = int(len(X) * 0.8)
        X_train = X[:split]
        y_train = y[:split]
        X_test  = X[split:]
        y_test  = y[split:]

        model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            verbosity=0,
        )
        model.fit(X_train, y_train)

        accuracy      = float(accuracy_score(y_test, model.predict(X_test)))
        latest        = X[-1].reshape(1, -1)
        pred          = model.predict(latest)[0]
        prob          = model.predict_proba(latest)[0]

        # Feature importance
        importance = model.feature_importances_
        feat_imp   = {
            feature_cols[i]: round(float(importance[i]), 4)
            for i in range(len(feature_cols))
        }
        feat_imp = dict(sorted(feat_imp.items(), key=lambda x: x[1], reverse=True))

        # News-specific feature importance
        news_feature_names = [
            "overall_sentiment", "banking_sentiment", "it_sentiment",
            "energy_sentiment", "geo_risk_score", "risk_alert_count",
            "bullish_article_pct", "bearish_article_pct",
        ]
        news_importance = {
            k: v for k, v in feat_imp.items()
            if k in news_feature_names
        }
        total_news_impact = round(sum(news_importance.values()), 4)

        return {
            "model":               "XGBoost + News Features",
            "accuracy":            round(accuracy * 100, 2),
            "next_day_direction":  "UP" if pred == 1 else "DOWN",
            "confidence":          round(float(max(prob)) * 100, 2),
            "up_probability":      round(float(prob[1]) * 100, 2),
            "down_probability":    round(float(prob[0]) * 100, 2),
            "feature_importance":  feat_imp,
            "news_feature_importance": news_importance,
            "total_news_impact":   total_news_impact,
            "top_features":        list(feat_imp.keys())[:5],
            "news_features_used":  news_features,
            "interpretation": _interpret_prediction(
                pred, prob, news_features, feat_imp
            ),
        }

    except Exception as e:
        logger.error(f"News-driven XGBoost failed: {e}")
        return {"error": str(e)}


def _build_enhanced_features(
    df: pd.DataFrame,
    news_features: Dict,
    macro_data: Dict = None,
) -> pd.DataFrame:
    """Builds enhanced feature matrix with news features."""
    features = pd.DataFrame(index=df.index)

    # Technical features
    features["returns"]        = df["close"].pct_change()
    features["returns_5d"]     = df["close"].pct_change(5)
    features["returns_20d"]    = df["close"].pct_change(20)
    features["volatility_20d"] = features["returns"].rolling(20, min_periods=1).std()
    features["sma_ratio"]      = df["close"] / df["close"].rolling(20, min_periods=1).mean()
    features["price_momentum"] = df["close"].pct_change(10)

    # RSI
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss  = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs    = gain / loss.replace(0, np.nan)
    features["rsi"] = (100 - (100 / (1 + rs))).fillna(50)

    # News features (same value for all rows — current news state)
    for key, value in news_features.items():
        features[key] = float(value)

    # Macro features
    if macro_data:
        features["usd_inr"]   = float(macro_data.get("forex", {}).get("usd_inr", 83.5))
        features["crude_oil"] = float(macro_data.get("commodities", {}).get("crude_oil_usd", 75))
    else:
        features["usd_inr"]   = 83.5
        features["crude_oil"] = 75.0

    # Target
    features["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    return features.dropna()


def _interpret_prediction(
    pred: int,
    prob: np.ndarray,
    news_features: Dict,
    feat_imp: Dict,
) -> str:
    """Generates plain English interpretation of prediction."""
    direction  = "UP" if pred == 1 else "DOWN"
    confidence = round(float(max(prob)) * 100, 1)
    geo_risk   = news_features.get("geo_risk_score", 0)
    sentiment  = news_features.get("overall_sentiment", 0)

    interpretation = f"Model predicts market will go {direction} tomorrow with {confidence}% confidence. "

    if geo_risk > 0.5:
        interpretation += f"High geopolitical risk (score: {geo_risk:.2f}) is a major headwind. "
    if sentiment < -0.2:
        interpretation += "Negative news sentiment is weighing on prediction. "
    elif sentiment > 0.2:
        interpretation += "Positive news sentiment is supporting upward prediction. "

    top_feature = list(feat_imp.keys())[0] if feat_imp else "price momentum"
    interpretation += f"Primary driver: {top_feature.replace('_', ' ')}."

    return interpretation


def generate_investment_signal(
    price_df: pd.DataFrame,
    news_data: Dict,
    risk_profile: str = "Moderate",
    macro_data: Dict = None,
) -> Dict:
    """
    Generates a complete investment signal combining:
    - ARIMA price prediction
    - XGBoost direction prediction
    - News sentiment
    - Geopolitical risk
    - Market regime
    Returns actionable recommendation.
    """
    from app.data.processing.data_processor import detect_market_regime_from_data

    news_features  = calculate_news_features(news_data)
    regime_data    = detect_market_regime_from_data(price_df)
    arima_result   = news_adjusted_arima_prediction(price_df["close"], news_data, 30)
    xgb_result     = news_driven_xgboost_prediction(price_df, news_data, macro_data)

    # Scoring system
    score = 0.0

    # ARIMA signal
    if "summary" in arima_result:
        if arima_result["summary"]["direction"] == "UP":
            score += 1.0
        else:
            score -= 1.0

    # XGBoost signal
    if "next_day_direction" in xgb_result:
        xgb_conf = xgb_result.get("confidence", 50) / 100
        if xgb_result["next_day_direction"] == "UP":
            score += xgb_conf
        else:
            score -= xgb_conf

    # News sentiment signal
    sentiment = news_features["overall_sentiment"]
    score    += sentiment * 2

    # Geopolitical risk penalty
    geo_risk  = news_features["geo_risk_score"]
    score    -= geo_risk * 2

    # Regime signal
    regime    = regime_data["regime"]
    regime_scores = {
        "Bull Market":      +1.5,
        "Recovery":         +0.5,
        "Sideways/Neutral":  0.0,
        "High Volatility":  -0.5,
        "Bear Market":      -1.5,
    }
    score += regime_scores.get(regime, 0)

    # Normalize score to -5 to +5
    score = max(-5, min(5, score))

    # Generate signal
    if score >= 2:
        signal      = "STRONG BUY"
        color       = "green"
        equity_adj  = +0.15
    elif score >= 0.5:
        signal      = "BUY"
        color       = "lightgreen"
        equity_adj  = +0.08
    elif score >= -0.5:
        signal      = "HOLD"
        color       = "yellow"
        equity_adj  = 0.0
    elif score >= -2:
        signal      = "SELL"
        color       = "orange"
        equity_adj  = -0.08
    else:
        signal      = "STRONG SELL"
        color       = "red"
        equity_adj  = -0.15

    # Risk profile adjustment
    profile_multipliers = {
        "Conservative": 0.5,
        "Moderate":     1.0,
        "Aggressive":   1.5,
    }
    equity_adj *= profile_multipliers.get(risk_profile, 1.0)

    return {
        "signal":           signal,
        "color":            color,
        "score":            round(score, 3),
        "equity_adjustment": round(equity_adj, 3),
        "regime":           regime,
        "news_sentiment":   round(sentiment, 4),
        "geo_risk":         round(geo_risk, 4),
        "risk_profile":     risk_profile,
        "components": {
            "arima_direction":    arima_result.get("summary", {}).get("direction", "N/A"),
            "xgboost_direction":  xgb_result.get("next_day_direction", "N/A"),
            "regime":             regime,
            "news_score":         round(sentiment, 4),
            "geo_risk_score":     round(geo_risk, 4),
        },
        "recommendation": _get_signal_recommendation(signal, equity_adj, regime, geo_risk),
        "generated_at":    datetime.now().isoformat(),
    }


def _get_signal_recommendation(
    signal: str,
    equity_adj: float,
    regime: str,
    geo_risk: float,
) -> str:
    base = {
        "STRONG BUY":  "Strong bullish signals across all models. Consider increasing equity allocation significantly.",
        "BUY":         "Positive signals detected. Gradual increase in equity exposure recommended.",
        "HOLD":        "Mixed signals. Maintain current allocation and monitor closely.",
        "SELL":        "Negative signals detected. Consider reducing equity exposure.",
        "STRONG SELL": "Strong bearish signals. Immediate de-risking recommended.",
    }.get(signal, "Monitor situation.")

    if geo_risk > 0.5:
        base += f" Warning: High geopolitical risk detected (score: {geo_risk:.2f}). Increase gold allocation."
    if regime == "Bear Market":
        base += " Market in Bear regime — prioritize capital preservation."

    return base