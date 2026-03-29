"""
ET Markets — Watchlist API
Smart watchlist with signal-aware priority sorting.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.state import app_state

router = APIRouter()

WATCHLIST_FILE = Path(__file__).parent.parent.parent / "mock_data" / "watchlist.json"

DEFAULT_WATCHLIST = [
    {"ticker": "RELIANCE.NS",  "stock": "Reliance Industries", "sector": "Energy",         "added": "2026-01-10"},
    {"ticker": "HDFCBANK.NS",  "stock": "HDFC Bank",           "sector": "Banking",        "added": "2026-01-15"},
    {"ticker": "INFY.NS",      "stock": "Infosys",             "sector": "IT",             "added": "2026-02-01"},
    {"ticker": "BAJFINANCE.NS","stock": "Bajaj Finance",       "sector": "NBFC",           "added": "2026-02-10"},
    {"ticker": "TATAMOTORS.NS","stock": "Tata Motors",         "sector": "Auto",           "added": "2026-03-01"},
]


def _load_watchlist():
    if WATCHLIST_FILE.exists():
        try:
            return json.loads(WATCHLIST_FILE.read_text())
        except Exception:
            pass
    return list(DEFAULT_WATCHLIST)


def _save_watchlist(data: list):
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_FILE.write_text(json.dumps(data, indent=2))


def _enrich_watchlist(items: list) -> list:
    """Attach live signal info to each watchlist entry."""
    signals = app_state.get_signals()
    import random

    enriched = []
    for item in items:
        stock_signals = [s for s in signals if s.get("stock") == item["stock"]]
        best_signal = max(stock_signals, key=lambda s: s.get("confidence", 0), default=None)

        rng = random.Random(sum(ord(c) for c in item["stock"]))
        price = round(rng.uniform(300, 4500), 2)
        change = round(rng.uniform(-3.0, 3.5), 2)

        enriched.append({
            **item,
            "current_price":  price,
            "change_pct":     change,
            "signal_count":   len(stock_signals),
            "top_signal":     best_signal.get("signal") if best_signal else None,
            "top_confidence": best_signal.get("confidence") if best_signal else None,
            "alert": "High confidence signal detected!" if best_signal and best_signal.get("confidence", 0) >= 0.80 else None,
            "timestamp": datetime.now().isoformat(),
        })

    # Sort: stocks with active high-confidence signals first
    enriched.sort(key=lambda x: (-(x["top_confidence"] or 0), x["stock"]))
    return enriched


class WatchlistAddRequest(BaseModel):
    ticker: str
    stock: str
    sector: Optional[str] = "Unknown"


@router.get("/watchlist", tags=["Watchlist"])
async def get_watchlist():
    """Return enriched watchlist with live signal alerts."""
    wl = _load_watchlist()
    return {
        "items":     _enrich_watchlist(wl),
        "count":     len(wl),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/watchlist", tags=["Watchlist"])
async def add_to_watchlist(req: WatchlistAddRequest):
    """Add a stock to the watchlist."""
    wl = _load_watchlist()
    if any(w["ticker"].lower() == req.ticker.lower() for w in wl):
        return {"success": False, "message": f"{req.stock} already in watchlist"}
    wl.append({
        "ticker":  req.ticker,
        "stock":   req.stock,
        "sector":  req.sector,
        "added":   datetime.now().strftime("%Y-%m-%d"),
    })
    _save_watchlist(wl)
    return {"success": True, "message": f"{req.stock} added to watchlist"}


@router.delete("/watchlist/{ticker}", tags=["Watchlist"])
async def remove_from_watchlist(ticker: str):
    """Remove a stock from the watchlist."""
    wl = _load_watchlist()
    original_len = len(wl)
    wl = [w for w in wl if w["ticker"].lower() != ticker.lower()]
    if len(wl) == original_len:
        return {"success": False, "message": f"Ticker {ticker} not found in watchlist"}
    _save_watchlist(wl)
    return {"success": True, "message": f"{ticker} removed from watchlist"}
