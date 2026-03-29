"""
ET Markets Intelligence Layer — Signal Scoring Engine

Combines signals from all 5 detectors into a unified scored output.

Weights:
  NLP signal:        0.30
  Candlestick:       0.20
  Anomaly:           0.20
  Options:           0.15
  Social sentiment:  0.15

Output: unified confidence, risk level (High/Medium/Low), strength (1-5 stars)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Source weights ───────────────────────────────────────────────────────────
SOURCE_WEIGHTS = {
    "NLP":             0.30,
    "Candlestick":     0.20,
    "Anomaly":         0.20,
    "Options":         0.15,
    "SocialSentiment": 0.15,
}

# ─── Signal type → primary source mapping ────────────────────────────────────
SIGNAL_SOURCE_MAP = {
    "EarningsRisk":        "NLP",
    "InsiderActivity":     "NLP",
    "SentimentShift":      "NLP",
    "MacroRisk":           "NLP",
    "UpgradeDowngrade":    "NLP",
    "FundamentalChange":   "NLP",
    "BullishReversal":     "Candlestick",
    "BearishReversal":     "Candlestick",
    "BullishContinuation": "Candlestick",
    "BearishContinuation": "Candlestick",
    "NeutralReversal":     "Candlestick",
    "VolumeSpike":         "Anomaly",
    "PriceSpike":          "Anomaly",
    "PriceDump":           "Anomaly",
    "BollingerBreachUp":   "Anomaly",
    "BollingerBreachDown": "Anomaly",
    "VolatilitySurge":     "Anomaly",
    "AboveVWAP":           "Anomaly",
    "BelowVWAP":           "Anomaly",
    "HighPCR":             "Options",
    "UnusualCallOI":       "Options",
    "MaxPainSupport":      "Options",
    "IVCrushRisk":         "Options",
    "IVSkewBearish":       "Options",
    "IVSkewBullish":       "Options",
    "SentimentSurge":      "SocialSentiment",
    "SentimentCrash":      "SocialSentiment",
    "ViralMention":        "SocialSentiment",
}


def score_signal(
    signal: dict,
    supporting_signals: Optional[list[dict]] = None,
) -> dict:
    """
    Score a primary signal, optionally boosted by corroborating signals
    from other detectors.

    Args:
        signal: primary signal dict (must have 'signal', 'confidence')
        supporting_signals: list of signals from other detectors on the same stock

    Returns:
        Enriched signal dict with updated confidence, risk, strength,
        contributing_signals list
    """
    base_confidence = signal.get("confidence", 0.60)
    signal_type = signal.get("signal", "")
    primary_source = SIGNAL_SOURCE_MAP.get(signal_type, "NLP")

    # ── Gather corroborating signal scores ───────────────────────────────────
    weighted_sum = base_confidence * SOURCE_WEIGHTS.get(primary_source, 0.20)
    total_weight = SOURCE_WEIGHTS.get(primary_source, 0.20)
    contributing = [primary_source]

    if supporting_signals:
        for sup in supporting_signals:
            sup_type = sup.get("signal", "")
            sup_source = SIGNAL_SOURCE_MAP.get(sup_type, "Anomaly")

            # Skip same source (no double counting)
            if sup_source == primary_source:
                continue

            weight = SOURCE_WEIGHTS.get(sup_source, 0.15)
            sup_conf = sup.get("confidence", 0.50)
            weighted_sum += sup_conf * weight
            total_weight += weight
            contributing.append(sup_source)

    # ── Normalise ─────────────────────────────────────────────────────────────
    final_confidence = round(
        min(0.97, weighted_sum / total_weight if total_weight > 0 else base_confidence),
        2
    )

    # ── Corroboration bonus (+0.02 per additional confirming source) ──────────
    corroboration_bonus = min(0.06, len(set(contributing) - {primary_source}) * 0.02)
    final_confidence = round(min(0.97, final_confidence + corroboration_bonus), 2)

    # ── Risk classification ───────────────────────────────────────────────────
    if final_confidence >= 0.80:
        risk = "High"
    elif final_confidence >= 0.60:
        risk = "Medium"
    else:
        risk = "Low"

    # ── Strength (1-5 stars) ──────────────────────────────────────────────────
    strength = max(1, min(5, round(final_confidence * 5)))

    enriched = {
        **signal,
        "confidence": final_confidence,
        "risk": risk,
        "strength": strength,
        "contributing_signals": list(set(contributing)),
    }
    return enriched


def rank_signals(signals: list[dict], top_n: int = 10) -> list[dict]:
    """
    Sort signals by confidence descending, return top_n.
    De-duplicates by (stock, signal_type) keeping highest confidence.
    """
    # De-duplicate: keep highest confidence per (stock, signal) pair
    seen = {}
    for sig in signals:
        key = (sig.get("stock"), sig.get("signal"))
        if key not in seen or sig.get("confidence", 0) > seen[key].get("confidence", 0):
            seen[key] = sig

    ranked = sorted(seen.values(), key=lambda s: s.get("confidence", 0), reverse=True)
    return ranked[:top_n]


def classify_risk(confidence: float) -> str:
    if confidence >= 0.80:
        return "High"
    elif confidence >= 0.60:
        return "Medium"
    return "Low"
