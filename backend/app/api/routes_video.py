"""
ET Markets — AI Market Video Engine
Generates data-driven market summary scripts and animation data
for the frontend video player component.
"""

import random
from datetime import datetime, timedelta
from fastapi import APIRouter
from app.state import app_state

router = APIRouter()


def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%d %b %Y")


def _generate_daily_summary(signals: list) -> dict:
    """Generate today's market summary script from live signals."""
    high_conf = [s for s in signals if s.get("confidence", 0) >= 0.80]
    top_signals = sorted(high_conf, key=lambda s: s.get("confidence", 0), reverse=True)[:3]

    # Market mood
    bullish_ct = sum(1 for s in signals if "buy" in s.get("signal", "").lower()
                     or s.get("sentiment_score", 0) > 0.3)
    bearish_ct = len(signals) - bullish_ct
    mood = "bullish" if bullish_ct > bearish_ct else "bearish"
    mood_emoji = "🟢" if mood == "bullish" else "🔴"

    # NIFTY mock data
    nifty = 22847.50
    nifty_chg = round(random.uniform(-0.8, 1.2), 2)
    sensex = round(nifty * 3.31, 2)
    sensex_chg = round(nifty_chg * 0.97, 2)

    top_gainers = [
        {"stock": "Bajaj Finance", "change": 3.4, "ticker": "BAJFINANCE"},
        {"stock": "L&T",           "change": 2.8, "ticker": "LT"},
        {"stock": "Sun Pharma",    "change": 2.1, "ticker": "SUNPHARMA"},
        {"stock": "ICICI Bank",    "change": 1.9, "ticker": "ICICIBANK"},
        {"stock": "Titan Company", "change": 1.7, "ticker": "TITAN"},
    ]
    top_losers = [
        {"stock": "Wipro",         "change": -2.2, "ticker": "WIPRO"},
        {"stock": "Asian Paints",  "change": -1.8, "ticker": "ASIANPAINT"},
        {"stock": "ONGC",          "change": -1.2, "ticker": "ONGC"},
    ]

    sector_rotation = [
        {"sector": "IT",             "change": 1.8,  "signal": "Overweight"},
        {"sector": "Banking",        "change": 1.4,  "signal": "Overweight"},
        {"sector": "Infrastructure", "change": 2.1,  "signal": "Accumulate"},
        {"sector": "Pharma",         "change": 0.9,  "signal": "Neutral"},
        {"sector": "FMCG",           "change": -0.4, "signal": "Underweight"},
        {"sector": "Energy",         "change": -0.8, "signal": "Underweight"},
    ]

    # Script generation
    script_lines = [
        f"Good morning investors! Today is {_days_ago(0)}.",
        f"Markets opened {mood} today as NIFTY 50 trades at {nifty:,.2f}, {'up' if nifty_chg >= 0 else 'down'} {abs(nifty_chg)}%.",
        f"SENSEX at {sensex:,.2f}, reflecting {'+' if sensex_chg >= 0 else ''}{sensex_chg}% movement.",
    ]

    if top_signals:
        sig = top_signals[0]
        script_lines.append(
            f"Top AI signal today: {sig.get('stock', 'Unknown')} showing {sig.get('signal', 'activity')} "
            f"with {int(sig.get('confidence', 0.8) * 100)}% confidence."
        )

    script_lines += [
        f"Infrastructure sector leads gains with +2.1%, driven by government capex spending.",
        f"IT sector also performing well on strong deal wins and stable margins.",
        f"Bajaj Finance is today's top gainer, up 3.4% on strong AUM growth guidance.",
        f"Total AI signals detected today: {len(signals)}. High-confidence signals: {len(high_conf)}.",
        f"FII activity remains net positive — foreign investors continue to show confidence in India's growth story.",
        f"Watch RELIANCE and HDFC BANK for potential breakout setups this week.",
        f"That's your ET Markets AI summary for {_days_ago(0)}. Stay informed, invest wisely.",
    ]

    return {
        "date": _days_ago(0),
        "mood": mood,
        "mood_emoji": mood_emoji,
        "script": " ".join(script_lines),
        "script_lines": script_lines,
        "indices": {
            "nifty":       {"value": nifty,   "change": nifty_chg},
            "sensex":      {"value": sensex,  "change": sensex_chg},
            "bank_nifty":  {"value": 48321.0, "change": round(random.uniform(-0.5, 1.5), 2)},
            "nifty_midcap":{"value": 41230.0, "change": round(random.uniform(-0.3, 1.0), 2)},
        },
        "top_gainers":   top_gainers,
        "top_losers":    top_losers,
        "sector_rotation": sector_rotation,
        "signal_summary": {
            "total":      len(signals),
            "high_conf":  len(high_conf),
            "bullish":    bullish_ct,
            "bearish":    bearish_ct,
            "top_signals": [
                {
                    "stock":      s.get("stock"),
                    "signal":     s.get("signal"),
                    "confidence": s.get("confidence"),
                }
                for s in top_signals
            ],
        },
        "duration_seconds": 75,
        "timestamp": datetime.now().isoformat(),
    }


def _get_historical_videos() -> list:
    """Return mock historical video summaries."""
    return [
        {
            "id":    f"VID{i:03}",
            "date":  _days_ago(i),
            "title": f"Market Summary — {_days_ago(i)}",
            "mood":  random.choice(["bullish", "bearish", "neutral"]),
            "nifty_change": round(random.uniform(-1.5, 1.8), 2),
            "duration_seconds": random.randint(60, 90),
            "views": random.randint(120, 4200),
        }
        for i in range(1, 8)
    ]


@router.get("/video/daily", tags=["Market Video"])
async def get_daily_video():
    """Generate today's AI market summary video data."""
    signals = app_state.get_signals()
    summary = _generate_daily_summary(signals)
    return summary


@router.get("/video/history", tags=["Market Video"])
async def get_video_history():
    """Return list of historical market summary videos."""
    return {
        "videos": _get_historical_videos(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/video/race-chart", tags=["Market Video"])
async def get_race_chart_data():
    """Return animated bar-chart race data for top stocks over last 30 days."""
    stocks = [
        "Reliance", "HDFC Bank", "Infosys", "TCS", "ICICI Bank",
        "L&T", "Bajaj Finance", "Kotak Bank", "Sun Pharma", "Titan",
    ]
    frames = []
    base_prices = {s: random.uniform(500, 4000) for s in stocks}

    for day in range(30):
        frame_data = []
        for stock in stocks:
            drift = random.uniform(-0.02, 0.025)
            base_prices[stock] = base_prices[stock] * (1 + drift)
            frame_data.append({
                "stock": stock,
                "value": round(base_prices[stock], 2),
                "change_pct": round(drift * 100, 2),
            })
        frame_data.sort(key=lambda x: x["value"], reverse=True)
        frames.append({
            "date":   _days_ago(30 - day),
            "stocks": frame_data,
        })

    return {
        "frames": frames,
        "stocks": stocks,
        "timestamp": datetime.now().isoformat(),
    }
