"""
ET Markets Intelligence Layer — Candlestick Pattern Detector

Detects classical candlestick patterns using pandas-ta.

Bullish patterns: Hammer, BullishEngulfing, MorningStar, ThreeWhiteSoldiers
Bearish patterns: ShootingStarPattern, BearishEngulfing, EveningStar, ThreeBlackCrows
Neutral/Reversal: Doji, SpinningTop, HangingMan

Each pattern is mapped to a signal type and assigned a confidence score,
boosted when confirmed by above-average volume.
"""

import uuid
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Pattern → Signal Mapping ─────────────────────────────────────────────────
PATTERN_SIGNAL_MAP = {
    # Bullish
    "CDL_HAMMER": ("BullishReversal", "HammerPattern", 0.68),
    "CDL_ENGULFING": ("BullishReversal", "BullishEngulfing", 0.72),
    "CDL_MORNINGSTAR": ("BullishReversal", "MorningStar", 0.74),
    "CDL_3WHITESOLDIERS": ("BullishContinuation", "ThreeWhiteSoldiers", 0.76),
    "CDL_PIERCING": ("BullishReversal", "PiercingLine", 0.66),
    "CDL_INVERTEDHAMMER": ("BullishReversal", "InvertedHammer", 0.62),
    # Bearish
    "CDL_SHOOTINGSTAR": ("BearishReversal", "ShootingStarPattern", 0.68),
    "CDL_EVENINGSTAR": ("BearishReversal", "EveningStar", 0.74),
    "CDL_3BLACKCROWS": ("BearishContinuation", "ThreeBlackCrows", 0.76),
    "CDL_DARKCLOUDCOVER": ("BearishReversal", "DarkCloudCover", 0.66),
    "CDL_HANGINGMAN": ("BearishReversal", "HangingMan", 0.64),
    # Neutral / Reversal
    "CDL_DOJI_10_0.1": ("NeutralReversal", "Doji", 0.58),
    "CDL_SPINNINGTOP": ("NeutralReversal", "SpinningTop", 0.55),
}


def _manual_hammer(df: pd.DataFrame) -> pd.Series:
    """Manual hammer pattern (fallback if pandas-ta unavailable)."""
    body = abs(df["Close"] - df["Open"])
    candle_range = df["High"] - df["Low"]
    lower_wick = df[["Open", "Close"]].min(axis=1) - df["Low"]
    upper_wick = df["High"] - df[["Open", "Close"]].max(axis=1)
    is_hammer = (lower_wick >= 2 * body) & (upper_wick <= 0.2 * candle_range) & (body > 0)
    return is_hammer.astype(int) * 100


def _manual_engulfing(df: pd.DataFrame) -> pd.Series:
    """Manual bullish engulfing pattern."""
    result = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        if prev["Close"] < prev["Open"] and curr["Close"] > curr["Open"]:
            if curr["Open"] <= prev["Close"] and curr["Close"] >= prev["Open"]:
                result.iloc[i] = 100
    return result


def _manual_doji(df: pd.DataFrame) -> pd.Series:
    """Manual doji pattern (open ≈ close within 0.1% of candle range)."""
    body = abs(df["Close"] - df["Open"])
    candle_range = df["High"] - df["Low"]
    is_doji = body <= 0.1 * candle_range
    return is_doji.astype(int) * 100


def detect_patterns(
    df: pd.DataFrame,
    stock: str,
    ticker: str,
    sector: Optional[str] = None,
    lookback: int = 5,
) -> list[dict]:
    """
    Detect candlestick patterns in the last `lookback` candles.

    Args:
        df: OHLCV DataFrame with DatetimeIndex
        stock: stock symbol
        ticker: NSE ticker
        sector: NIFTY sector
        lookback: number of recent candles to check for patterns

    Returns:
        List of detected pattern signal dicts
    """
    if df is None or len(df) < 14:
        return []

    signals = []
    avg_volume = df["Volume"].rolling(20).mean().iloc[-1]

    try:
        import pandas_ta as ta
        # Run pandas-ta CDL patterns (subset that's available)
        df_ta = df.copy()
        df_ta.ta.cdl_pattern(name="all", append=True)

        for col, (signal_type, pattern_name, base_conf) in PATTERN_SIGNAL_MAP.items():
            if col in df_ta.columns:
                # Look at last `lookback` candles for pattern signal
                recent = df_ta[col].iloc[-lookback:]
                hits = recent[recent != 0]
                if not hits.empty:
                    # Most recent hit
                    hit_idx = hits.index[-1]
                    hit_candle = df_ta.loc[hit_idx]

                    # Volume confirmation bonus
                    vol_ratio = hit_candle["Volume"] / avg_volume if avg_volume > 0 else 1.0
                    volume_confirmed = bool(vol_ratio > 1.5)
                    conf_bonus = 0.06 if volume_confirmed else 0.0
                    confidence = round(min(0.92, base_conf + conf_bonus), 2)

                    signals.append({
                        "id": f"sig_{uuid.uuid4().hex[:8]}",
                        "stock": stock,
                        "ticker": ticker,
                        "sector": sector,
                        "signal": signal_type,
                        "pattern": pattern_name,
                        "confidence": confidence,
                        "risk": "Medium" if confidence < 0.75 else "High",
                        "strength": round(confidence * 5),
                        "source": "PatternDetector",
                        "volume_confirmed": volume_confirmed,
                        "volume_ratio": round(float(vol_ratio), 2),
                        "detected_on": str(hit_idx.date()) if hasattr(hit_idx, "date") else str(hit_idx),
                        "contributing_signals": ["Candlestick"],
                        "timestamp": datetime.now().isoformat(),
                    })

    except ImportError:
        logger.warning("pandas-ta not available — using manual pattern detection")
        # ── Manual fallback ────────────────────────────────────────────────
        hammer = _manual_hammer(df)
        engulf = _manual_engulfing(df)
        doji = _manual_doji(df)

        for pattern_series, pattern_name, signal_type, base_conf in [
            (hammer, "HammerPattern", "BullishReversal", 0.65),
            (engulf, "BullishEngulfing", "BullishReversal", 0.70),
            (doji, "Doji", "NeutralReversal", 0.55),
        ]:
            recent = pattern_series.iloc[-lookback:]
            hits = recent[recent != 0]
            if not hits.empty:
                hit_idx = hits.index[-1]
                vol_at_hit = df.loc[hit_idx, "Volume"]
                vol_ratio = vol_at_hit / avg_volume if avg_volume > 0 else 1.0
                volume_confirmed = bool(vol_ratio > 1.5)
                confidence = round(min(0.88, base_conf + (0.06 if volume_confirmed else 0)), 2)
                signals.append({
                    "id": f"sig_{uuid.uuid4().hex[:8]}",
                    "stock": stock,
                    "ticker": ticker,
                    "sector": sector,
                    "signal": signal_type,
                    "pattern": pattern_name,
                    "confidence": confidence,
                    "risk": "Medium",
                    "strength": round(confidence * 5),
                    "source": "PatternDetector",
                    "volume_confirmed": volume_confirmed,
                    "volume_ratio": round(float(vol_ratio), 2),
                    "detected_on": str(hit_idx.date()) if hasattr(hit_idx, "date") else str(hit_idx),
                    "contributing_signals": ["Candlestick"],
                    "timestamp": datetime.now().isoformat(),
                })

    except Exception as e:
        logger.error(f"Pattern detection failed for {stock}: {e}")

    return signals
