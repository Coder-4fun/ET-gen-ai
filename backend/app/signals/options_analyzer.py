"""
ET Markets Intelligence Layer — Options Chain Analyzer

Analyzes NSE options chain data to surface institutional activity signals.

Metrics computed:
- PCR (Put-Call Ratio): PCR > 1.2 = bearish, PCR < 0.7 = bullish
- Max Pain: strike where option writers lose least
- OI Concentration: unusual OI buildup at specific strikes
- IV Skew: abnormal implied volatility differences across strikes
- IV Crush: post-event IV collapse detection

Signals generated:
- HighPCR (bearish institutional bet)
- UnusualCallOI (bullish positioning)
- MaxPainSupport (price gravity level)
- IVCrushRisk (post-earnings options warning)
"""

import uuid
import logging
from typing import Optional
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_pcr(chain: list[dict]) -> float:
    """Put-Call Ratio = total put OI / total call OI."""
    total_pe_oi = sum(row.get("pe_oi", 0) for row in chain)
    total_ce_oi = sum(row.get("ce_oi", 0) for row in chain)
    if total_ce_oi == 0:
        return 1.0
    return round(total_pe_oi / total_ce_oi, 4)


def compute_max_pain(chain: list[dict]) -> float:
    """
    Max Pain = strike where total option loss for writers is minimum.

    For each possible expiry strike, compute:
    - Total loss for call writers (all ITM calls losing)
    - Total loss for put writers (all ITM puts losing)
    Max pain = argmin of total writer pain.
    """
    if not chain:
        return 0.0

    strikes = [row["strike"] for row in chain]
    results = {}

    for test_strike in strikes:
        pain = 0
        for row in chain:
            s = row["strike"]
            # Call writer pain at test_strike
            if test_strike > s:
                pain += row.get("ce_oi", 0) * (test_strike - s)
            # Put writer pain at test_strike
            if test_strike < s:
                pain += row.get("pe_oi", 0) * (s - test_strike)
        results[test_strike] = pain

    return float(min(results, key=results.get))


def compute_iv_skew(chain: list[dict], spot: float) -> str:
    """
    Compute IV skew direction.
    Right-skewed = OTM puts have higher IV than OTM calls (bearish)
    Left-skewed = OTM calls higher (bullish/demand for upside)
    """
    otm_calls = [r for r in chain if r["strike"] > spot]
    otm_puts = [r for r in chain if r["strike"] < spot]

    if not otm_calls or not otm_puts:
        return "flat"

    avg_call_iv = np.mean([r.get("ce_iv", 15) for r in otm_calls[:3]])
    avg_put_iv = np.mean([r.get("pe_iv", 15) for r in otm_puts[-3:]])

    if avg_put_iv > avg_call_iv + 1.5:
        return "right-skewed"   # bears paying up for put protection
    elif avg_call_iv > avg_put_iv + 1.5:
        return "left-skewed"    # bulls buying calls aggressively
    else:
        return "flat"


def detect_unusual_oi(chain: list[dict]) -> Optional[dict]:
    """Detect strike with unusually high OI concentration."""
    if not chain:
        return None

    ce_ois = [r.get("ce_oi", 0) for r in chain]
    pe_ois = [r.get("pe_oi", 0) for r in chain]

    # Find strike with max OI
    max_ce_idx = int(np.argmax(ce_ois))
    max_pe_idx = int(np.argmax(pe_ois))

    max_ce_strike = chain[max_ce_idx]["strike"]
    max_pe_strike = chain[max_pe_idx]["strike"]

    return {
        "max_ce_strike": max_ce_strike,
        "max_ce_oi": ce_ois[max_ce_idx],
        "max_pe_strike": max_pe_strike,
        "max_pe_oi": pe_ois[max_pe_idx],
    }


def analyze_options_chain(
    chain: list[dict],
    stock: str,
    ticker: str,
    spot_price: float,
    sector: Optional[str] = None,
    expiry: Optional[str] = None,
) -> list[dict]:
    """
    Full options chain analysis pipeline.

    Args:
        chain: list of strike dicts with CE/PE OI, volume, IV, LTP
        stock: stock symbol
        ticker: NSE ticker
        spot_price: current spot price
        sector: NIFTY sector
        expiry: option expiry date string

    Returns:
        List of options-based signal dicts
    """
    if not chain:
        return []

    signals = []

    try:
        pcr = compute_pcr(chain)
        max_pain = compute_max_pain(chain)
        iv_skew = compute_iv_skew(chain, spot_price)
        oi_concentration = detect_unusual_oi(chain)

        base_meta = {
            "stock": stock,
            "ticker": ticker,
            "sector": sector,
            "source": "OptionsAnalyzer",
            "pcr": pcr,
            "max_pain": max_pain,
            "iv_skew": iv_skew,
            "contributing_signals": ["Options"],
            "timestamp": datetime.now().isoformat(),
        }

        # ── PCR Signal ────────────────────────────────────────────────────
        if pcr > 1.2:
            confidence = min(0.92, 0.60 + (pcr - 1.2) * 0.4)
            signals.append({
                **base_meta,
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "signal": "HighPCR",
                "confidence": round(confidence, 2),
                "risk": "High" if confidence >= 0.80 else "Medium",
                "strength": round(confidence * 5),
                "explanation": f"High PCR of {pcr:.2f} indicates heavy put buying — bearish institutional positioning.",
            })
        elif pcr < 0.7:
            confidence = min(0.88, 0.60 + (0.7 - pcr) * 0.5)
            signals.append({
                **base_meta,
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "signal": "UnusualCallOI",
                "confidence": round(confidence, 2),
                "risk": "Low" if confidence < 0.70 else "Medium",
                "strength": round(confidence * 5),
                "explanation": f"Low PCR of {pcr:.2f} indicates call buying dominance — bullish institutional positioning.",
            })

        # ── Max Pain Support Signal ────────────────────────────────────────
        if max_pain > 0:
            mp_distance_pct = abs(spot_price - max_pain) / spot_price * 100
            if mp_distance_pct < 3.0:  # Spot near max pain
                confidence = round(0.65 + (3.0 - mp_distance_pct) * 0.05, 2)
                signals.append({
                    **base_meta,
                    "id": f"sig_{uuid.uuid4().hex[:8]}",
                    "signal": "MaxPainSupport",
                    "confidence": min(0.82, confidence),
                    "risk": "Low",
                    "strength": 3,
                    "explanation": f"Spot price ₹{spot_price:,.0f} is near max pain ₹{max_pain:,.0f} — price gravity zone ahead of expiry.",
                })

        # ── IV Skew Signal ─────────────────────────────────────────────────
        if iv_skew == "right-skewed":
            signals.append({
                **base_meta,
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "signal": "IVSkewBearish",
                "confidence": 0.66,
                "risk": "Medium",
                "strength": 3,
                "explanation": "OTM puts have significantly higher IV than calls — market pricing in downside risk.",
            })
        elif iv_skew == "left-skewed":
            signals.append({
                **base_meta,
                "id": f"sig_{uuid.uuid4().hex[:8]}",
                "signal": "IVSkewBullish",
                "confidence": 0.64,
                "risk": "Low",
                "strength": 3,
                "explanation": "OTM calls have higher IV — demand for upside coverage is elevated.",
            })

    except Exception as e:
        logger.error(f"Options analysis failed for {stock}: {e}")

    return signals


def get_options_summary(chain: list[dict], spot_price: float, stock: str) -> dict:
    """Quick summary dict for the options chain endpoint."""
    pcr = compute_pcr(chain)
    max_pain = compute_max_pain(chain)
    iv_skew = compute_iv_skew(chain, spot_price)

    if pcr > 1.2:
        signal = "HighPCR"
        signal_bias = "Bearish"
        confidence = round(min(0.92, 0.60 + (pcr - 1.2) * 0.4), 2)
        interpretation = f"Heavy put buying (PCR {pcr:.2f}) suggests institutional bearish hedging near spot ₹{spot_price:,.0f}."
    elif pcr < 0.7:
        signal = "UnusualCallOI"
        signal_bias = "Bullish"
        confidence = round(min(0.88, 0.60 + (0.7 - pcr) * 0.5), 2)
        interpretation = f"Call buying dominance (PCR {pcr:.2f}) indicates bullish institutional positioning."
    else:
        signal = "NeutralPositioning"
        signal_bias = "Neutral"
        confidence = 0.50
        interpretation = f"PCR of {pcr:.2f} is in neutral territory — no clear directional bias."

    return {
        "stock": stock,
        "pcr": pcr,
        "max_pain": max_pain,
        "iv_skew": iv_skew,
        "signal": signal,
        "signal_bias": signal_bias,
        "confidence": confidence,
        "interpretation": interpretation,
    }
