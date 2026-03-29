"""
ET Markets Intelligence Layer v2 — Signal Correlator

Deduplicates redundant signals and correlates weak signals
into composite high-confidence signals.

No Redis required — works with in-memory storage for hackathon mode.
Falls back gracefully when Redis is unavailable.
"""

import json
import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ─── In-memory fallback stores ────────────────────────────────────────────────
_dedup_cache: dict[str, datetime] = {}     # fingerprint → timestamp
_signal_windows: dict[str, list] = defaultdict(list)  # symbol → [recent signals]


class SignalCorrelator:
    """
    Deduplicates redundant signals and correlates weak signals
    into composite high-confidence signals.
    
    Works in two modes:
    - Redis mode: uses Redis for dedup cache + correlation windows
    - Memory mode: uses in-memory dicts (default/fallback)
    """

    DEDUP_WINDOW = 300          # 5 minutes: same stock + event type = duplicate
    CORRELATION_WINDOW = 86400  # 24 hours: different signal types on same stock
    COMPOSITE_THRESHOLD = 3     # 3+ signals → composite
    COMPOSITE_BOOST = 1.35      # composite score multiplier (capped at 0.97)

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.use_redis = redis_client is not None

    def get_signal_fingerprint(self, signal: dict) -> str:
        """
        Create a fingerprint for deduplication.
        Same stock + same signal type + same directional bias within 5 minutes = duplicate.
        """
        stock = signal.get("stock", "")
        signal_type = signal.get("signal", "")
        # Determine directional bias from signal type
        bias = self._get_bias(signal_type)
        key = f"{stock}:{signal_type}:{bias}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_bias(self, signal_type: str) -> str:
        """Determine directional bias from signal type."""
        bullish = {
            "BullishReversal", "BullishContinuation", "UnusualCallOI",
            "SentimentSurge", "UpgradeDowngrade", "FundamentalChange",
            "AboveVWAP", "BollingerBreachUp", "IVSkewBullish", "ViralMention",
            "PriceSpike", "MaxPainSupport",
        }
        bearish = {
            "BearishReversal", "BearishContinuation", "HighPCR",
            "SentimentCrash", "BollingerBreachDown", "BelowVWAP",
            "IVSkewBearish", "IVCrushRisk", "PriceDump", "EarningsRisk",
        }
        if signal_type in bullish:
            return "bullish"
        if signal_type in bearish:
            return "bearish"
        return "neutral"

    async def is_duplicate(self, signal: dict) -> bool:
        """Check if an identical signal was fired in the dedup window."""
        fp = self.get_signal_fingerprint(signal)

        if self.use_redis:
            try:
                key = f"signal:dedup:{fp}"
                exists = await self.redis.exists(key)
                if not exists:
                    await self.redis.setex(key, self.DEDUP_WINDOW, "1")
                return bool(exists)
            except Exception as e:
                logger.warning(f"Redis dedup check failed ({e}), using memory")

        # In-memory fallback
        now = datetime.now()
        if fp in _dedup_cache:
            elapsed = (now - _dedup_cache[fp]).total_seconds()
            if elapsed < self.DEDUP_WINDOW:
                return True
        _dedup_cache[fp] = now

        # Cleanup old entries
        cutoff = now - timedelta(seconds=self.DEDUP_WINDOW * 2)
        expired = [k for k, v in _dedup_cache.items() if v < cutoff]
        for k in expired:
            del _dedup_cache[k]

        return False

    async def check_correlation(self, signal: dict) -> Optional[dict]:
        """
        Check if this signal, combined with recent signals on same stock,
        creates a composite high-confidence signal.
        """
        stock = signal.get("stock", "")
        signal_type = signal.get("signal", "")
        confidence = signal.get("confidence", 0.5)
        bias = self._get_bias(signal_type)
        now = datetime.now()

        # Get source category for this signal
        source = signal.get("source", "")

        new_entry = {
            "type": signal_type,
            "source": source,
            "confidence": confidence,
            "bias": bias,
            "ts": now.isoformat(),
        }

        if self.use_redis:
            try:
                window_key = f"signal:window:{stock}"
                recent_raw = await self.redis.lrange(window_key, 0, -1)
                recent = [json.loads(r) for r in recent_raw]

                await self.redis.lpush(window_key, json.dumps(new_entry))
                await self.redis.expire(window_key, self.CORRELATION_WINDOW)
            except Exception as e:
                logger.warning(f"Redis correlation failed ({e}), using memory")
                recent = _signal_windows.get(stock, [])
                _signal_windows[stock].append(new_entry)
        else:
            recent = _signal_windows.get(stock, [])
            _signal_windows[stock].append(new_entry)

        # Cleanup old in-memory entries (>24h)
        cutoff = now - timedelta(seconds=self.CORRELATION_WINDOW)
        _signal_windows[stock] = [
            r for r in _signal_windows.get(stock, [])
            if datetime.fromisoformat(r["ts"]) > cutoff
        ]

        # Filter: same bias, different signal types (from different detectors)
        same_bias = [
            r for r in recent
            if r["bias"] == bias
            and r["type"] != signal_type  # different signal types only
        ]

        # De-duplicate by source type to avoid counting same detector twice
        unique_sources = set()
        unique_corroborating = []
        for r in same_bias:
            src_key = r.get("source", r["type"])
            if src_key not in unique_sources:
                unique_sources.add(src_key)
                unique_corroborating.append(r)

        if len(unique_corroborating) >= self.COMPOSITE_THRESHOLD - 1:
            # Build composite signal
            all_confs = [r["confidence"] for r in unique_corroborating] + [confidence]
            composite_conf = min(0.97, sum(all_confs) / len(all_confs) * self.COMPOSITE_BOOST)
            all_types = [r["type"] for r in unique_corroborating] + [signal_type]

            return {
                **signal,
                "is_composite": True,
                "confidence": round(composite_conf, 2),
                "signal": "CompositeSignal",
                "original_signal": signal_type,
                "composite_sources": list(set(all_types)),
                "composite_count": len(all_types),
                "risk": "High" if composite_conf >= 0.80 else "Medium",
                "strength": min(5, round(composite_conf * 5)),
                "explanation": (
                    f"COMPOSITE SIGNAL: {len(set(all_types))} independent detectors converge "
                    f"({', '.join(set(all_types))}) on {stock} — "
                    f"confidence boosted to {composite_conf:.0%}"
                ),
            }

        return None

    async def process(self, signal: dict) -> Optional[dict]:
        """
        Full dedup + correlation pipeline.
        Returns None if duplicate, composite signal if correlated,
        original signal otherwise.
        """
        if await self.is_duplicate(signal):
            logger.debug(f"Dropped duplicate signal: {signal.get('stock')} / {signal.get('signal')}")
            return None

        composite = await self.check_correlation(signal)
        if composite:
            logger.info(
                f"🔗 Composite signal created: {composite.get('stock')} — "
                f"{composite.get('composite_count')} sources → {composite.get('confidence'):.0%}"
            )
            return composite

        return signal


# Module-level singleton
_correlator: Optional[SignalCorrelator] = None


def get_correlator(redis_client=None) -> SignalCorrelator:
    """Get or create the singleton correlator instance."""
    global _correlator
    if _correlator is None:
        _correlator = SignalCorrelator(redis_client)
    return _correlator
