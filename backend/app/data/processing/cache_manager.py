import json
import redis
from typing import Any, Optional, Dict
from datetime import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connected successfully")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    REDIS_AVAILABLE = False
    redis_client   = None

# In-memory fallback cache
_memory_cache: Dict[str, Any] = {}


def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Stores value in Redis cache with TTL in seconds.
    Falls back to memory cache if Redis unavailable.
    """
    try:
        serialized = json.dumps(value, default=str)
        if REDIS_AVAILABLE and redis_client:
            redis_client.setex(key, ttl, serialized)
        else:
            _memory_cache[key] = {
                "value":      value,
                "expires_at": datetime.now().timestamp() + ttl,
            }
        return True
    except Exception as e:
        logger.error(f"Cache set failed for {key}: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Retrieves value from Redis cache.
    Falls back to memory cache if Redis unavailable.
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
        else:
            cached = _memory_cache.get(key)
            if cached and cached["expires_at"] > datetime.now().timestamp():
                return cached["value"]
        return None
    except Exception as e:
        logger.error(f"Cache get failed for {key}: {e}")
        return None


def delete_cache(key: str) -> bool:
    """Deletes a cache key."""
    try:
        if REDIS_AVAILABLE and redis_client:
            redis_client.delete(key)
        else:
            _memory_cache.pop(key, None)
        return True
    except Exception as e:
        logger.error(f"Cache delete failed for {key}: {e}")
        return False


def cache_market_summary(data: Dict) -> bool:
    """Caches market summary for 5 minutes."""
    return set_cache("market:summary", data, ttl=300)


def get_cached_market_summary() -> Optional[Dict]:
    """Gets cached market summary."""
    return get_cache("market:summary")


def cache_nifty_history(period: str, data: Dict) -> bool:
    """Caches NIFTY history for 1 hour."""
    return set_cache(f"market:nifty:{period}", data, ttl=3600)


def get_cached_nifty_history(period: str) -> Optional[Dict]:
    """Gets cached NIFTY history."""
    return get_cache(f"market:nifty:{period}")


def cache_news_sentiment(data: Dict) -> bool:
    """Caches news sentiment for 1 hour."""
    return set_cache("market:news:sentiment", data, ttl=3600)


def get_cached_news_sentiment() -> Optional[Dict]:
    """Gets cached news sentiment."""
    return get_cache("market:news:sentiment")


def cache_fund_data(scheme_code: str, data: Dict) -> bool:
    """Caches mutual fund data for 24 hours."""
    return set_cache(f"fund:{scheme_code}", data, ttl=86400)


def get_cached_fund_data(scheme_code: str) -> Optional[Dict]:
    """Gets cached fund data."""
    return get_cache(f"fund:{scheme_code}")


def cache_stock_price(symbol: str, data: Dict) -> bool:
    """Caches stock price for 5 minutes."""
    return set_cache(f"stock:{symbol}", data, ttl=300)


def get_cached_stock_price(symbol: str) -> Optional[Dict]:
    """Gets cached stock price."""
    return get_cache(f"stock:{symbol}")