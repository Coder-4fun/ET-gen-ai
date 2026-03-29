"""
ET Markets Intelligence Layer — Statistical Anomaly Detector

Detects price and volume anomalies using statistical methods:
1. Z-score: flag if |z| > 2.5 on volume or price change
2. Rolling volatility: 5-day realized vol vs 20-day average
3. Bollinger Band breach: close outside 2-std bands
4. Intraday VWAP deviation: price > 2% from VWAP
"""

import uuid
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def compute_bollinger_bands(series: pd.Series, window: int = 20, std_mult: float = 2.0) -> tuple:
    """Returns (upper_band, middle_band, lower_band) for a price series."""
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return sma + std_mult * std, sma, sma - std_mult * std


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """Compute Volume Weighted Average Price."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()


def compute_z_score(series: pd.Series, window: int = 20) -> pd.Series:
    """Rolling Z-score = (value - rolling_mean) / rolling_std."""
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    return (series - rolling_mean) / (rolling_std + 1e-9)


def detect_anomalies(
    df: pd.DataFrame,
    stock: str,
    ticker: str,
    sector: Optional[str] = None,
    z_threshold: float = 2.5,
    vwap_deviation_pct: float = 2.0,
) -> list[dict]:
    """
    Run all anomaly detectors on an OHLCV DataFrame.

    Args:
        df: DataFrame with columns Open, High, Low, Close, Volume (DatetimeIndex)
        stock: stock symbol
        ticker: NSE ticker
        sector: NIFTY sector
        z_threshold: Z-score threshold for flagging anomalies
        vwap_deviation_pct: % deviation from VWAP to flag

    Returns:
        List of detected anomaly signal dicts
    """
    if df is None or len(df) < 20:
        return []

    signals = []

    try:
        # ── 1. Volume Z-score ─────────────────────────────────────────────
        vol_z = compute_z_score(df["Volume"])
        latest_vol_z = vol_z.iloc[-1]
        volume_ratio = df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1]

        if abs(latest_vol_z) > z_threshold:
            confidence = min(0.95, 0.60 + abs(latest_vol_z) * 0.06)
            signals.append({
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "stock": stock,
                "ticker": ticker,
                "sector": sector,
                "signal": "VolumeSpike",
                "confidence": round(confidence, 2),
                "risk": "High" if confidence >= 0.80 else "Medium",
                "strength": round(confidence * 5),
                "source": "AnomalyDetector",
                "z_score": round(float(latest_vol_z), 2),
                "volume_ratio": round(float(volume_ratio), 2),
                "contributing_signals": ["Anomaly"],
                "timestamp": datetime.now().isoformat(),
            })

        # ── 2. Price Z-score (daily return) ──────────────────────────────
        returns = df["Close"].pct_change()
        price_z = compute_z_score(returns)
        latest_price_z = price_z.iloc[-1]

        if abs(latest_price_z) > z_threshold:
            direction = "PriceSpike" if latest_price_z > 0 else "PriceDump"
            confidence = min(0.90, 0.55 + abs(latest_price_z) * 0.05)
            signals.append({
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "stock": stock,
                "ticker": ticker,
                "sector": sector,
                "signal": direction,
                "confidence": round(confidence, 2),
                "risk": "High" if confidence >= 0.80 else "Medium",
                "strength": round(confidence * 5),
                "source": "AnomalyDetector",
                "z_score": round(float(latest_price_z), 2),
                "contributing_signals": ["Anomaly"],
                "timestamp": datetime.now().isoformat(),
            })

        # ── 3. Bollinger Band Breach ──────────────────────────────────────
        upper, mid, lower = compute_bollinger_bands(df["Close"])
        last_close = df["Close"].iloc[-1]
        last_upper = upper.iloc[-1]
        last_lower = lower.iloc[-1]

        if last_close > last_upper or last_close < last_lower:
            breach_type = "BollingerBreachUp" if last_close > last_upper else "BollingerBreachDown"
            pct_outside = abs(last_close - (last_upper if last_close > last_upper else last_lower)) / last_close * 100
            confidence = min(0.90, 0.60 + pct_outside * 0.08)
            signals.append({
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "stock": stock,
                "ticker": ticker,
                "sector": sector,
                "signal": breach_type,
                "confidence": round(confidence, 2),
                "risk": "Medium",
                "strength": round(confidence * 5),
                "source": "AnomalyDetector",
                "contributing_signals": ["Anomaly"],
                "timestamp": datetime.now().isoformat(),
            })

        # ── 4. Rolling Volatility Regime ─────────────────────────────────
        realized_vol_5d = returns.rolling(5).std().iloc[-1] * np.sqrt(252)
        avg_vol_20d = returns.rolling(20).std().mean() * np.sqrt(252)

        if realized_vol_5d > avg_vol_20d * 1.8:  # 80% above average
            confidence = min(0.85, 0.55 + (realized_vol_5d / avg_vol_20d - 1) * 0.15)
            signals.append({
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "stock": stock,
                "ticker": ticker,
                "sector": sector,
                "signal": "VolatilitySurge",
                "confidence": round(confidence, 2),
                "risk": "Medium",
                "strength": round(confidence * 5),
                "source": "AnomalyDetector",
                "contributing_signals": ["Anomaly"],
                "timestamp": datetime.now().isoformat(),
            })

        # ── 5. VWAP Deviation (intraday) ─────────────────────────────────
        try:
            vwap = compute_vwap(df)
            last_vwap = vwap.iloc[-1]
            vwap_dev_pct = (last_close - last_vwap) / last_vwap * 100
            if abs(vwap_dev_pct) > vwap_deviation_pct:
                direction = "AboveVWAP" if vwap_dev_pct > 0 else "BelowVWAP"
                confidence = min(0.80, 0.55 + abs(vwap_dev_pct) * 0.04)
                signals.append({
                    "id": f"sig_{uuid.uuid4().hex[:8]}",
                    "stock": stock,
                    "ticker": ticker,
                    "sector": sector,
                    "signal": direction,
                    "confidence": round(confidence, 2),
                    "risk": "Low",
                    "strength": round(confidence * 5),
                    "source": "AnomalyDetector",
                    "contributing_signals": ["Anomaly"],
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Anomaly detection failed for {stock}: {e}")

    return signals
