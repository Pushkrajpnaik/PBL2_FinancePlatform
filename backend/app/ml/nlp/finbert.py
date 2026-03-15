import torch
import numpy as np
from typing import Dict, List, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FinBERT Model
# ---------------------------------------------------------------------------
FINBERT_MODEL = "ProsusAI/finbert"

_tokenizer = None
_model     = None
_device    = None


def load_finbert():
    """
    Loads FinBERT model and tokenizer.
    Downloads on first run (~500MB), cached after.
    """
    global _tokenizer, _model, _device

    if _tokenizer is not None and _model is not None:
        return True

    try:
        logger.info("Loading FinBERT model...")
        _device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
        _model     = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
        _model     = _model.to(_device)
        _model.eval()
        logger.info(f"FinBERT loaded successfully on {_device}")
        return True
    except Exception as e:
        logger.error(f"Failed to load FinBERT: {e}")
        return False


def analyze_with_finbert(text: str) -> Dict:
    """
    Analyzes a single text using FinBERT.
    Returns sentiment scores for positive, negative, neutral.
    """
    if not load_finbert():
        return _fallback_sentiment(text)

    try:
        # Truncate to 512 tokens max
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(_device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = _model(**inputs)
            scores  = torch.nn.functional.softmax(outputs.logits, dim=-1)
            scores  = scores.cpu().numpy()[0]

        # FinBERT labels: positive=0, negative=1, neutral=2
        labels = _model.config.id2label
        result = {labels[i].lower(): float(scores[i]) for i in range(len(scores))}

        # Determine dominant sentiment
        sentiment_map = {
            "positive": result.get("positive", 0),
            "negative": result.get("negative", 0),
            "neutral":  result.get("neutral", 0),
        }
        dominant   = max(sentiment_map, key=sentiment_map.get)
        confidence = float(max(sentiment_map.values()))

        # Convert to compound score (-1 to +1)
        compound = float(
            result.get("positive", 0) - result.get("negative", 0)
        )

        return {
            "sentiment":   dominant.capitalize(),
            "compound":    round(compound, 4),
            "confidence":  round(confidence, 4),
            "scores": {
                "positive": round(result.get("positive", 0), 4),
                "negative": round(result.get("negative", 0), 4),
                "neutral":  round(result.get("neutral", 0), 4),
            },
            "model": "FinBERT",
        }

    except Exception as e:
        logger.error(f"FinBERT inference failed: {e}")
        return _fallback_sentiment(text)


def analyze_batch_finbert(texts: List[str], batch_size: int = 8) -> List[Dict]:
    """
    Analyzes multiple texts in batches for efficiency.
    """
    if not load_finbert():
        return [_fallback_sentiment(t) for t in texts]

    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            inputs = _tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(_device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = _model(**inputs)
                scores  = torch.nn.functional.softmax(outputs.logits, dim=-1)
                scores  = scores.cpu().numpy()

            labels = _model.config.id2label
            for j, score in enumerate(scores):
                result = {labels[k].lower(): float(score[k]) for k in range(len(score))}
                dominant  = max(result, key=result.get)
                compound  = float(result.get("positive", 0) - result.get("negative", 0))
                results.append({
                    "sentiment":  dominant.capitalize(),
                    "compound":   round(compound, 4),
                    "confidence": round(float(max(result.values())), 4),
                    "scores": {
                        "positive": round(result.get("positive", 0), 4),
                        "negative": round(result.get("negative", 0), 4),
                        "neutral":  round(result.get("neutral", 0), 4),
                    },
                    "model": "FinBERT",
                })
        except Exception as e:
            logger.error(f"Batch FinBERT failed: {e}")
            for text in batch:
                results.append(_fallback_sentiment(text))

    return results


def _fallback_sentiment(text: str) -> Dict:
    """VADER fallback if FinBERT unavailable."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader    = SentimentIntensityAnalyzer()
        scores   = vader.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            sentiment = "Positive"
        elif compound <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        return {
            "sentiment":  sentiment,
            "compound":   round(compound, 4),
            "confidence": round(abs(compound), 4),
            "scores": {
                "positive": round(scores["pos"], 4),
                "negative": round(scores["neg"], 4),
                "neutral":  round(scores["neu"], 4),
            },
            "model": "VADER (fallback)",
        }
    except Exception:
        return {
            "sentiment":  "Neutral",
            "compound":   0.0,
            "confidence": 0.0,
            "scores":     {"positive": 0, "negative": 0, "neutral": 1},
            "model":      "fallback",
        }