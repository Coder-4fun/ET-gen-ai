"""
ET Markets Intelligence Layer v2 — Cache Strategy

Coordinated caching hierarchy for all data endpoints.
Works in two modes:
- Redis mode: uses Redis with TTL-based expiry
- Memory mode: uses in-memory dict with timestamp tracking (fallback)
"""

import json
import time
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

# ─── TTL hierarchy for all cached data ────────────────────────────────────────
CACHE_STRATEGY = {
    # Tier 1: Live data (30-60 seconds)
    "nse:quote:{symbol}":           60,
    "nse:orderbook:{symbol}":       30,
    "signal:live:{symbol}":         60,
    "options:chain:{symbol}":       120,

    # Tier 2: Near-real-time (5 minutes)
    "sector:performance":           300,
    "fii:dii:flows":                300,
    "portfolio:{user_id}":          300,
    "signal:list:{filters_hash}":   300,
    "market:nifty":                 120,
    "market:bulk":                  120,
    "heatmap:data":                 120,

    # Tier 3: Slow-changing (15-60 minutes)
    "nse:universe":                 86400,   # 24h — refreshed daily
    "signal:accuracy:stats":        3600,    # 1h
    "earnings:calendar":            900,     # 15 mins
    "backtesting:results:{id}":     3600,    # 1h
    "alpha:scores":                 300,     # 5 mins
    "radar:events":                 600,     # 10 mins
    "video:daily":                  600,     # 10 mins

    # Tier 4: Static (daily refresh)
    "nifty50:constituents":         86400,
    "regime:current":               300,
}

# ─── In-Memory Cache Store ───────────────────────────────────────────────────

_memory_cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_time)


class CacheManager:
    """
    Universal cache-through manager.
    Supports Redis (preferred) and in-memory fallback.
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.use_redis = redis_client is not None
        self._hit_count = 0
        self._miss_count = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache. Returns None on miss."""
        # Try Redis first
        if self.use_redis:
            try:
                raw = await self.redis.get(key)
                if raw:
                    self._hit_count += 1
                    return json.loads(raw)
            except Exception as e:
                logger.debug(f"Redis get failed for {key}: {e}")

        # Fall back to memory
        if key in _memory_cache:
            value, expire_time = _memory_cache[key]
            if time.time() < expire_time:
                self._hit_count += 1
                return value
            else:
                del _memory_cache[key]

        self._miss_count += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set cache with TTL."""
        # Try Redis
        if self.use_redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception as e:
                logger.debug(f"Redis set failed for {key}: {e}")

        # Fall back to memory
        _memory_cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str):
        """Remove from cache."""
        if self.use_redis:
            try:
                await self.redis.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)

    async def get_or_compute(self, key: str, compute_fn: Callable, ttl: int = 300) -> Any:
        """Universal cache-through: get from cache, compute on miss."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        result = await compute_fn()
        await self.set(key, result, ttl)
        return result

    def get_stats(self) -> dict:
        """Get cache hit/miss statistics."""
        total = self._hit_count + self._miss_count
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": round(self._hit_count / total * 100, 1) if total else 0,
            "total_requests": total,
            "memory_keys": len(_memory_cache),
            "backend": "redis" if self.use_redis else "memory",
        }

    async def clear_all(self):
        """Clear all caches (use cautiously)."""
        _memory_cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        if self.use_redis:
            try:
                await self.redis.flushdb()
            except Exception:
                pass

    def cleanup_expired(self):
        """Remove expired entries from memory cache."""
        now = time.time()
        expired = [k for k, (_, exp) in _memory_cache.items() if now >= exp]
        for k in expired:
            del _memory_cache[k]
        if expired:
            logger.debug(f"Cache cleanup: removed {len(expired)} expired entries")


# ─── Module singleton ────────────────────────────────────────────────────────
_cache_manager: Optional[CacheManager] = None


def get_cache(redis_client=None) -> CacheManager:
    """Get or create the singleton cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(redis_client)
    return _cache_manager
