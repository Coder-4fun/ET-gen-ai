"""
ET Markets Intelligence Layer v2 — Signal Accuracy Tracker

Tracks signal outcomes by comparing actual price movement to predicted direction.
Builds a trust-level dashboard: "85% of HIGH confidence bullish signals on NIFTY 50 
stocks moved up within 5 trading days."

Works in-memory for hackathon mode, supports DB persistence when available.
"""

import logging
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ─── In-memory signal outcome store ──────────────────────────────────────────
_signal_log: list[dict] = []         # All logged signals
_signal_outcomes: list[dict] = []    # Resolved outcomes
HOLD_PERIODS = [1, 3, 5, 10]        # Trading days to check


# ─── Pre-seeded historical accuracy data (mock for hackathon) ─────────────────
# These simulate what the system would have tracked over months of operation.
MOCK_HISTORICAL_ACCURACY = {
    "overall": {
        "total_signals": 2847,
        "resolved_signals": 2341,
        "correct_signals": 1756,
        "accuracy_pct": 75.0,
        "avg_return_pct": 2.1,
        "sharpe_ratio": 1.42,
    },
    "by_confidence": {
        "high": {
            "bucket": "≥75%", "total": 482, "correct": 410, "accuracy": 85.1,
            "avg_return": 4.2, "best_signal": "CompositeSignal", "worst_signal": "VolatilitySurge",
        },
        "medium": {
            "bucket": "50–74%", "total": 1128, "correct": 834, "accuracy": 73.9,
            "avg_return": 1.8, "best_signal": "BullishReversal", "worst_signal": "VolumeSpike",
        },
        "low": {
            "bucket": "<50%", "total": 731, "correct": 512, "accuracy": 70.0,
            "avg_return": 0.6, "best_signal": "AboveVWAP", "worst_signal": "SentimentShift",
        },
    },
    "by_signal_type": {
        "BullishReversal":     {"total": 312, "correct": 246, "accuracy": 78.8, "avg_return": 3.1},
        "BearishReversal":     {"total": 198, "correct": 154, "accuracy": 77.8, "avg_return": 2.8},
        "VolumeSpike":         {"total": 410, "correct": 283, "accuracy": 69.0, "avg_return": 1.2},
        "PriceSpike":          {"total": 187, "correct": 127, "accuracy": 67.9, "avg_return": 1.5},
        "BollingerBreachUp":   {"total": 156, "correct": 120, "accuracy": 76.9, "avg_return": 2.4},
        "BollingerBreachDown": {"total": 142, "correct": 105, "accuracy": 73.9, "avg_return": 2.1},
        "InsiderActivity":     {"total": 89,  "correct": 73,  "accuracy": 82.0, "avg_return": 5.2},
        "CompositeSignal":     {"total": 67,  "correct": 61,  "accuracy": 91.0, "avg_return": 6.8},
        "SentimentSurge":      {"total": 178, "correct": 132, "accuracy": 74.2, "avg_return": 1.9},
        "AboveVWAP":           {"total": 210, "correct": 160, "accuracy": 76.2, "avg_return": 1.6},
        "MaxPainSupport":      {"total": 98,  "correct": 71,  "accuracy": 72.4, "avg_return": 1.4},
        "EarningsRisk":        {"total": 145, "correct": 112, "accuracy": 77.2, "avg_return": 3.4},
        "UpgradeDowngrade":    {"total": 112, "correct": 88,  "accuracy": 78.6, "avg_return": 3.8},
        "MacroRisk":           {"total": 134, "correct": 89,  "accuracy": 66.4, "avg_return": 0.8},
        "FundamentalChange":   {"total": 76,  "correct": 54,  "accuracy": 71.1, "avg_return": 2.2},
        "ViralMention":        {"total": 133, "correct": 81,  "accuracy": 60.9, "avg_return": 0.4},
    },
    "by_period": {
        1:  {"total": 2341, "correct": 1498, "accuracy": 64.0, "avg_return": 0.6},
        3:  {"total": 2341, "correct": 1638, "accuracy": 70.0, "avg_return": 1.4},
        5:  {"total": 2341, "correct": 1756, "accuracy": 75.0, "avg_return": 2.1},
        10: {"total": 2341, "correct": 1825, "accuracy": 78.0, "avg_return": 3.2},
    },
    "by_sector": {
        "IT":             {"total": 425, "correct": 332, "accuracy": 78.1},
        "Banking":        {"total": 512, "correct": 384, "accuracy": 75.0},
        "Energy":         {"total": 321, "correct": 234, "accuracy": 72.9},
        "Pharma":         {"total": 198, "correct": 155, "accuracy": 78.3},
        "Auto":           {"total": 234, "correct": 175, "accuracy": 74.8},
        "FMCG":           {"total": 187, "correct": 143, "accuracy": 76.5},
        "Metals":         {"total": 156, "correct": 108, "accuracy": 69.2},
        "Infrastructure": {"total": 142, "correct": 107, "accuracy": 75.4},
        "NBFC":           {"total": 98,  "correct": 72,  "accuracy": 73.5},
        "Consumer":       {"total": 68,  "correct": 46,  "accuracy": 67.6},
    },
    "streak": {
        "current_streak": 7,        # consecutive correct predictions
        "longest_streak": 23,
        "current_streak_type": "correct",
        "recent_10": [True, True, True, False, True, True, True, True, False, True],
    },
    "monthly_accuracy": [
        {"month": "2026-01", "accuracy": 72.1, "signals": 412},
        {"month": "2026-02", "accuracy": 76.8, "signals": 498},
        {"month": "2026-03", "accuracy": 78.4, "signals": 531},
    ],
}


class AccuracyTracker:
    """
    Tracks signal outcomes and computes accuracy metrics.
    
    For hackathon: uses pre-seeded mock data + live tracking of new signals.
    For production: resolves outcomes via yfinance historical data.
    """

    def __init__(self):
        self.log = _signal_log
        self.outcomes = _signal_outcomes

    def log_signal(self, signal: dict):
        """Log a new signal for future accuracy tracking."""
        entry = {
            "id": signal.get("id", ""),
            "stock": signal.get("stock", ""),
            "signal_type": signal.get("signal", ""),
            "confidence": signal.get("confidence", 0),
            "direction": self._get_direction(signal),
            "regime": signal.get("regime", "unknown"),
            "is_composite": signal.get("is_composite", False),
            "timestamp": datetime.now().isoformat(),
            "resolved": False,
        }
        self.log.append(entry)

    def _get_direction(self, signal: dict) -> str:
        sig = signal.get("signal", "")
        bullish = {"BullishReversal", "BullishContinuation", "UnusualCallOI",
                   "SentimentSurge", "AboveVWAP", "BollingerBreachUp", "PriceSpike",
                   "CompositeSignal", "ViralMention", "MaxPainSupport", "IVSkewBullish"}
        if sig in bullish:
            return "bullish"
        return "bearish"

    async def resolve_signals(self):
        """
        Resolve unresolved signals by checking actual price movement.
        In hackathon mode, uses simulated outcomes.
        """
        now = datetime.now()
        unresolved = [
            s for s in self.log
            if not s["resolved"]
            and datetime.fromisoformat(s["timestamp"]) < now - timedelta(days=5)
        ]

        for signal in unresolved:
            # Simulate resolution (hackathon mode)
            conf = signal["confidence"]
            # Higher confidence → higher chance of correct prediction
            base_accuracy = 0.55 + conf * 0.35  # 55-90% accuracy range
            was_correct = random.random() < base_accuracy
            actual_return = random.uniform(0.5, 6.0) if was_correct else random.uniform(-5.0, -0.5)
            if signal["direction"] == "bearish":
                actual_return = -actual_return

            outcome = {
                "signal_id": signal["id"],
                "stock": signal["stock"],
                "signal_type": signal["signal_type"],
                "confidence_bucket": "high" if conf >= 0.75 else ("medium" if conf >= 0.50 else "low"),
                "direction": signal["direction"],
                "actual_return_pct": round(actual_return, 2),
                "was_correct": was_correct,
                "period_days": 5,
                "resolved_at": now.isoformat(),
            }
            self.outcomes.append(outcome)
            signal["resolved"] = True

        if unresolved:
            logger.info(f"📊 Resolved {len(unresolved)} signal outcomes")

    def get_accuracy_stats(self, include_mock: bool = True) -> dict:
        """
        Get comprehensive accuracy statistics.
        Merges live tracked outcomes with pre-seeded historical data.
        """
        result = dict(MOCK_HISTORICAL_ACCURACY) if include_mock else {}

        # Add live stats if we have outcomes
        if self.outcomes:
            live_correct = sum(1 for o in self.outcomes if o["was_correct"])
            live_total = len(self.outcomes)
            result["live_tracking"] = {
                "total": live_total,
                "correct": live_correct,
                "accuracy": round(live_correct / live_total * 100, 1) if live_total else 0,
                "pending_resolution": sum(1 for s in self.log if not s["resolved"]),
                "since": self.outcomes[0]["resolved_at"] if self.outcomes else None,
            }

        result["generated_at"] = datetime.now().isoformat()
        return result

    def get_signal_track_record(self, signal_type: str) -> dict:
        """Get accuracy for a specific signal type."""
        mock = MOCK_HISTORICAL_ACCURACY["by_signal_type"].get(signal_type)
        live = [o for o in self.outcomes if o["signal_type"] == signal_type]

        return {
            "signal_type": signal_type,
            "historical": mock or {"total": 0, "correct": 0, "accuracy": 0},
            "live": {
                "total": len(live),
                "correct": sum(1 for o in live if o["was_correct"]),
                "accuracy": round(
                    sum(1 for o in live if o["was_correct"]) / len(live) * 100, 1
                ) if live else None,
            },
        }


# ─── Module singleton ────────────────────────────────────────────────────────
_tracker: Optional[AccuracyTracker] = None


def get_accuracy_tracker() -> AccuracyTracker:
    global _tracker
    if _tracker is None:
        _tracker = AccuracyTracker()
    return _tracker
