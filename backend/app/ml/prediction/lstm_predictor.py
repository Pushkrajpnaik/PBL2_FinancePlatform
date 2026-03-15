import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


def prepare_lstm_data(
    series: np.ndarray,
    lookback: int = 60,
) -> tuple:
    """
    Prepares sequences for LSTM training.
    lookback = number of past days to use for prediction
    """
    X, y = [], []
    for i in range(lookback, len(series)):
        X.append(series[i - lookback:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def build_lstm_model(lookback: int, features: int = 1):
    """Builds a simple LSTM model."""
    try:
        import torch
        import torch.nn as nn

        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
                super(LSTMModel, self).__init__()
                self.lstm = nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    dropout=dropout,
                    batch_first=True,
                )
                self.dropout = nn.Dropout(dropout)
                self.fc      = nn.Linear(hidden_size, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                out    = self.dropout(out[:, -1, :])
                out    = self.fc(out)
                return out

        return LSTMModel(input_size=features)

    except Exception as e:
        logger.error(f"Failed to build LSTM: {e}")
        return None


def predict_lstm(
    price_series: pd.Series,
    forecast_days: int = 30,
    lookback: int = 60,
    epochs: int = 20,
) -> Dict:
    """
    Predicts future prices using LSTM on real historical data.
    Uses PyTorch for training.
    """
    try:
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import MinMaxScaler

        if len(price_series) < lookback + 10:
            return {"error": f"Need at least {lookback + 10} data points for LSTM"}

        prices = price_series.values.reshape(-1, 1).astype(float)

        # Normalize
        scaler      = MinMaxScaler(feature_range=(0, 1))
        scaled      = scaler.fit_transform(prices)

        # Prepare sequences
        X, y = prepare_lstm_data(scaled.flatten(), lookback=lookback)
        X    = torch.FloatTensor(X).unsqueeze(-1)
        y    = torch.FloatTensor(y).unsqueeze(-1)

        # Build and train model
        model     = build_lstm_model(lookback=lookback)
        if model is None:
            return {"error": "Could not build LSTM model"}

        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        model.train()
        losses = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            output = model(X)
            loss   = criterion(output, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss.item()))

        logger.info(f"LSTM trained for {epochs} epochs. Final loss: {losses[-1]:.6f}")

        # Generate predictions
        model.eval()
        last_price    = float(price_series.iloc[-1])
        predictions   = []
        current_seq   = scaled[-lookback:].flatten().tolist()

        with torch.no_grad():
            for _ in range(forecast_days):
                seq    = torch.FloatTensor(current_seq[-lookback:]).unsqueeze(0).unsqueeze(-1)
                pred   = model(seq)
                pred_val = float(pred.item())
                current_seq.append(pred_val)
                # Inverse transform
                pred_price = float(scaler.inverse_transform([[pred_val]])[0][0])
                predictions.append(pred_price)

        # Generate dates
        future_dates = [
            (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
            for i in range(forecast_days)
        ]

        # Add uncertainty bands (±2% per week)
        forecast_with_ci = []
        for i, (date, price) in enumerate(zip(future_dates, predictions)):
            uncertainty = price * 0.02 * (i // 5 + 1)
            forecast_with_ci.append({
                "date":        date,
                "price":       round(price, 2),
                "lower_bound": round(price - uncertainty, 2),
                "upper_bound": round(price + uncertainty, 2),
            })

        final_price     = predictions[-1]
        expected_return = ((final_price / last_price) - 1) * 100

        return {
            "model":         "LSTM (PyTorch)",
            "current_price": round(last_price, 2),
            "forecast_days": forecast_days,
            "lookback_days": lookback,
            "epochs_trained": epochs,
            "final_loss":    round(losses[-1], 6),
            "predictions":   forecast_with_ci,
            "summary": {
                "predicted_price_30d": round(final_price, 2),
                "expected_return_30d": round(expected_return, 2),
                "direction":           "UP" if expected_return > 0 else "DOWN",
                "confidence":          "High" if losses[-1] < 0.001 else "Medium",
            },
        }

    except Exception as e:
        logger.error(f"LSTM prediction failed: {e}")
        return {"error": str(e)}