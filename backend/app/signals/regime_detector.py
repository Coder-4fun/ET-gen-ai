"""
ET Markets Intelligence Layer v2 — Market Regime Detector

Detects current market regime using Nifty 50 data.
Used to calibrate signal confidence scores — a bullish breakout
in a strong bear market should be dampened, and vice versa.

Regime types: strong_bull, weak_bull, sideways, weak_bear, strong_bear
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Regime(str, Enum):
    STRONG_BULL = "strong_bull"
    WEAK_BULL = "weak_bull"
    SIDEWAYS = "sideways"
    WEAK_BEAR = "weak_bear"
    STRONG_BEAR = "strong_bear"


@dataclass
class RegimeResult:
    regime: Regime
    confidence: float          # 0-1
    signal_multiplier: float   # applied to bullish signals (inverse for bearish)
    key_indicators: dict
    score: float               # raw regime score


# Regime multipliers: how much to boost/dampen bullish vs bearish signals
REGIME_MULTIPLIERS = {
    # In a strong bull, bullish signals get 1.3x confidence boost
    Regime.STRONG_BULL:  {"bullish": 1.30, "bearish": 0.70, "neutral": 1.0},
    Regime.WEAK_BULL:    {"bullish": 1.10, "bearish": 0.85, "neutral": 1.0},
    Regime.SIDEWAYS:     {"bullish": 1.00, "bearish": 1.00, "neutral": 1.0},
    Regime.WEAK_BEAR:    {"bullish": 0.85, "bearish": 1.10, "neutral": 1.0},
    Regime.STRONG_BEAR:  {"bullish": 0.70, "bearish": 1.30, "neutral": 1.0},
}

# Directional bias classification for signal types
SIGNAL_BIAS = {
    "BullishReversal": "bullish",
    "BullishContinuation": "bullish",
    "UnusualCallOI": "bullish",
    "SentimentSurge": "bullish",
    "UpgradeDowngrade": "bullish",
    "FundamentalChange": "bullish",
    "AboveVWAP": "bullish",
    "BollingerBreachUp": "bullish",
    "IVSkewBullish": "bullish",
    "PriceSpike": "bullish",
    "MaxPainSupport": "bullish",
    "ViralMention": "bullish",
    "BearishReversal": "bearish",
    "BearishContinuation": "bearish",
    "HighPCR": "bearish",
    "SentimentCrash": "bearish",
    "BollingerBreachDown": "bearish",
    "BelowVWAP": "bearish",
    "IVSkewBearish": "bearish",
    "IVCrushRisk": "bearish",
    "PriceDump": "bearish",
    "EarningsRisk": "bearish",
    "VolumeSpike": "neutral",
    "VolatilitySurge": "neutral",
    "NeutralReversal": "neutral",
    "InsiderActivity": "neutral",
    "MacroRisk": "neutral",
    "SentimentShift": "neutral",
    "CompositeSignal": "neutral",
}


def _calc_adx(df: pd.DataFrame, period: int = 14) -> float:
    """Calculate Average Directional Index (ADX) for trend strength."""
    try:
        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1 / period, adjust=False).mean()

        dm_plus = ((high - high.shift()) > (low.shift() - low)) * (high - high.shift()).clip(lower=0)
        dm_minus = ((low.shift() - low) > (high - high.shift())) * (low.shift() - low).clip(lower=0)

        di_plus = 100 * dm_plus.ewm(alpha=1 / period, adjust=False).mean() / (atr + 1e-9)
        di_minus = 100 * dm_minus.ewm(alpha=1 / period, adjust=False).mean() / (atr + 1e-9)

        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus + 1e-9)
        adx = dx.ewm(alpha=1 / period, adjust=False).mean()

        return float(adx.iloc[-1])
    except Exception as e:
        logger.warning(f"ADX calculation failed: {e}")
        return 20.0  # neutral default


def detect_regime(nifty_data: pd.DataFrame) -> RegimeResult:
    """
    Multi-factor regime detection using Nifty 50 OHLCV data.

    Uses 4 factors:
    1. Price vs 200 DMA — trend direction
    2. 20-day return momentum — near-term strength
    3. ADX — trend conviction
    4. Realized volatility — risk/fear factor

    Args:
        nifty_data: DataFrame with Open, High, Low, Close, Volume columns

    Returns:
        RegimeResult with regime, confidence, and signal multiplier
    """
    if nifty_data is None or len(nifty_data) < 30:
        return RegimeResult(
            regime=Regime.SIDEWAYS,
            confidence=0.3,
            signal_multiplier=1.0,
            key_indicators={"error": "Insufficient data"},
            score=0.0,
        )

    close = nifty_data["Close"]

    # Factor 1: Price vs 200 DMA (if enough data, else use 50 DMA)
    ma_period = 200 if len(close) >= 200 else min(50, len(close) - 1)
    ma = close.rolling(ma_period).mean().iloc[-1]
    current = close.iloc[-1]
    above_ma = (current - ma) / ma  # e.g., +0.05 = 5% above MA

    # Factor 2: 20-day return momentum
    lookback = min(20, len(close) - 1)
    momentum = (current / close.iloc[-lookback] - 1) if lookback > 0 else 0

    # Factor 3: ADX (trend strength)
    adx = _calc_adx(nifty_data, period=14)

    # Factor 4: Realized volatility (annualized)
    returns = close.pct_change().dropna()
    vol_window = min(20, len(returns))
    realized_vol = float(returns.iloc[-vol_window:].std() * np.sqrt(252)) if vol_window > 1 else 0.15

    # ── Composite regime score: -2 (strong bear) to +2 (strong bull) ──────
    score = 0.0
    score += float(np.clip(above_ma * 10, -1, 1))        # ±1 from MA position
    score += float(np.clip(momentum * 15, -1, 1))         # ±1 from momentum
    score += 0.5 if adx > 25 else -0.25                   # trending = confidence
    score -= float(np.clip((realized_vol - 0.15) * 5, 0, 0.5))  # high vol = slight bear bias

    # ── Classify regime ───────────────────────────────────────────────────
    if score > 1.2:
        regime = Regime.STRONG_BULL
    elif score > 0.4:
        regime = Regime.WEAK_BULL
    elif score > -0.4:
        regime = Regime.SIDEWAYS
    elif score > -1.2:
        regime = Regime.WEAK_BEAR
    else:
        regime = Regime.STRONG_BEAR

    return RegimeResult(
        regime=regime,
        confidence=min(1.0, abs(score) / 2),
        signal_multiplier=REGIME_MULTIPLIERS[regime]["bullish"],
        key_indicators={
            f"nifty_vs_{ma_period}ma": f"{above_ma:+.1%}",
            "momentum_20d": f"{momentum:+.1%}",
            "adx": round(adx, 1),
            "realized_vol": f"{realized_vol:.1%}",
            "raw_score": round(score, 2),
        },
        score=round(score, 3),
    )


def apply_regime_to_signal(signal: dict, regime: RegimeResult) -> dict:
    """
    Adjust a signal's confidence score based on the current market regime.

    In a strong bull market:
    - Bullish signals get boosted (×1.3)
    - Bearish signals get dampened (×0.7)

    In a strong bear market:
    - Bearish signals get boosted (×1.3)
    - Bullish signals get dampened (×0.7)
    """
    signal_type = signal.get("signal", "")
    bias = SIGNAL_BIAS.get(signal_type, "neutral")
    multipliers = REGIME_MULTIPLIERS.get(regime.regime, REGIME_MULTIPLIERS[Regime.SIDEWAYS])
    multiplier = multipliers.get(bias, 1.0)

    original_conf = signal.get("confidence", 0.5)
    adjusted_conf = min(0.97, round(original_conf * multiplier, 2))

    # Reclassify risk after adjustment
    if adjusted_conf >= 0.80:
        risk = "High"
    elif adjusted_conf >= 0.60:
        risk = "Medium"
    else:
        risk = "Low"

    enriched = {
        **signal,
        "confidence": adjusted_conf,
        "risk": risk,
        "strength": max(1, min(5, round(adjusted_conf * 5))),
        "regime_adjusted": True,
        "regime": regime.regime.value,
        "regime_confidence": round(regime.confidence, 2),
    }

    if adjusted_conf != original_conf:
        enriched["regime_note"] = (
            f"Confidence adjusted {original_conf:.0%}→{adjusted_conf:.0%} "
            f"for {regime.regime.value} market regime"
        )

    return enriched


# ─── Cached regime result ─────────────────────────────────────────────────────
_cached_regime: Optional[RegimeResult] = None
_cached_regime_ts: Optional[float] = None
REGIME_CACHE_TTL = 300  # 5 minutes


def get_current_regime(nifty_data: pd.DataFrame = None) -> RegimeResult:
    """
    Get current regime, using cache if fresh.
    If no nifty_data provided, returns cached or default SIDEWAYS.
    """
    global _cached_regime, _cached_regime_ts
    import time

    now = time.time()
    if _cached_regime and _cached_regime_ts and (now - _cached_regime_ts) < REGIME_CACHE_TTL:
        return _cached_regime

    if nifty_data is not None and len(nifty_data) > 20:
        _cached_regime = detect_regime(nifty_data)
        _cached_regime_ts = now
        logger.info(
            f"📊 Market regime detected: {_cached_regime.regime.value} "
            f"(confidence: {_cached_regime.confidence:.0%}, "
            f"multiplier: {_cached_regime.signal_multiplier:.2f})"
        )
        return _cached_regime

    return RegimeResult(
        regime=Regime.SIDEWAYS,
        confidence=0.3,
        signal_multiplier=1.0,
        key_indicators={},
        score=0.0,
    )
