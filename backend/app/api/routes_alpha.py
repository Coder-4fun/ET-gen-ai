"""
ET Markets — Alpha Score Engine
Computes a weighted composite Alpha Score (0–100) per stock:
  Institutional Buying  25%
  Technical Breakout    25%
  NLP Sentiment         25%
  Earnings Growth       25%
"""

import random
from datetime import datetime
from fastapi import APIRouter
from app.state import app_state

router = APIRouter()

# Curated universe for scoring
ALPHA_UNIVERSE = [
    {"stock": "Reliance Industries", "ticker": "RELIANCE.NS", "sector": "Energy"},
    {"stock": "HDFC Bank",           "ticker": "HDFCBANK.NS",  "sector": "Banking"},
    {"stock": "Infosys",             "ticker": "INFY.NS",      "sector": "IT"},
    {"stock": "TCS",                 "ticker": "TCS.NS",       "sector": "IT"},
    {"stock": "ICICI Bank",          "ticker": "ICICIBANK.NS", "sector": "Banking"},
    {"stock": "Wipro",               "ticker": "WIPRO.NS",     "sector": "IT"},
    {"stock": "L&T",                 "ticker": "LT.NS",        "sector": "Infrastructure"},
    {"stock": "Kotak Mahindra Bank", "ticker": "KOTAKBANK.NS", "sector": "Banking"},
    {"stock": "Bajaj Finance",       "ticker": "BAJFINANCE.NS","sector": "NBFC"},
    {"stock": "HUL",                 "ticker": "HINDUNILVR.NS","sector": "FMCG"},
    {"stock": "Asian Paints",        "ticker": "ASIANPAINT.NS","sector": "Consumer"},
    {"stock": "Titan Company",       "ticker": "TITAN.NS",     "sector": "Consumer"},
    {"stock": "Sun Pharma",          "ticker": "SUNPHARMA.NS", "sector": "Pharma"},
    {"stock": "Dr Reddy's",          "ticker": "DRREDDY.NS",   "sector": "Pharma"},
    {"stock": "Maruti Suzuki",       "ticker": "MARUTI.NS",    "sector": "Auto"},
    {"stock": "Tata Motors",         "ticker": "TATAMOTORS.NS","sector": "Auto"},
    {"stock": "ONGC",                "ticker": "ONGC.NS",      "sector": "Energy"},
    {"stock": "Power Grid",          "ticker": "POWERGRID.NS", "sector": "Utilities"},
    {"stock": "Adani Ports",         "ticker": "ADANIPORTS.NS","sector": "Infrastructure"},
    {"stock": "Tata Steel",          "ticker": "TATASTEEL.NS", "sector": "Metals"},
]

SIGNAL_LABELS = {
    (80, 100): ("Strong Buy",  "high",   "#10b981"),
    (65, 80):  ("Bullish",     "medium", "#06b6d4"),
    (50, 65):  ("Neutral-Up",  "low",    "#f59e0b"),
    (35, 50):  ("Neutral",     "low",    "#94a3b8"),
    (0, 35):   ("Caution",     "low",    "#f43f5e"),
}


def _label(score: float):
    for (lo, hi), (label, risk, color) in SIGNAL_LABELS.items():
        if lo <= score < hi or (hi == 100 and score == 100):
            return label, risk, color
    return "Neutral", "low", "#94a3b8"


def _compute_alpha(stock_info: dict, existing_signals: list) -> dict:
    """Fake-but-realistic Alpha Score computation."""
    name = stock_info["stock"]

    # Pull confidence from existing signals for this stock
    stock_signals = [s for s in existing_signals if s.get("stock") == name]
    signal_confidence = max((s.get("confidence", 0) for s in stock_signals), default=0)

    # Component scores (seeded by stock name for stable demo values + small random drift)
    seed = sum(ord(c) for c in name)
    rng = random.Random(seed + int(datetime.now().hour))

    institutional = round(rng.uniform(40, 95), 1)
    technical     = round(signal_confidence * 100 * 0.6 + rng.uniform(20, 40), 1)
    technical     = min(technical, 100)
    sentiment     = round(rng.uniform(35, 90), 1)
    earnings      = round(rng.uniform(30, 88), 1)

    alpha = round(
        0.25 * institutional +
        0.25 * technical     +
        0.25 * sentiment     +
        0.25 * earnings,
        1
    )

    label, risk, color = _label(alpha)

    return {
        **stock_info,
        "alpha_score": alpha,
        "signal_label": label,
        "risk": risk,
        "color": color,
        "components": {
            "institutional": institutional,
            "technical":     technical,
            "sentiment":     sentiment,
            "earnings":      earnings,
        },
        "active_signals": len(stock_signals),
        "signal_types":   list({s.get("signal", "") for s in stock_signals})[:3],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/alpha", tags=["Alpha Score"])
async def get_alpha_scores(limit: int = 20):
    """Return top N stocks ranked by Alpha Score."""
    signals = app_state.get_signals()
    scores = [_compute_alpha(s, signals) for s in ALPHA_UNIVERSE]
    scores.sort(key=lambda x: x["alpha_score"], reverse=True)
    return {
        "scores": scores[:limit],
        "total": len(scores),
        "timestamp": datetime.now().isoformat(),
        "legend": {
            "80-100": "Strong Buy",
            "65-79":  "Bullish",
            "50-64":  "Neutral-Up",
            "35-49":  "Neutral",
            "0-34":   "Caution",
        }
    }


@router.get("/alpha/{ticker}", tags=["Alpha Score"])
async def get_stock_alpha(ticker: str):
    """Return Alpha Score for a specific ticker."""
    info = next((s for s in ALPHA_UNIVERSE if s["ticker"].lower() == ticker.lower()
                 or s["stock"].lower() == ticker.lower()), None)
    if not info:
        return {"error": f"Stock '{ticker}' not found in alpha universe"}
    return _compute_alpha(info, app_state.get_signals())
