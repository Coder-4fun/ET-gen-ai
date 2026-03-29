"""
ET Markets — Live Market Data Routes

Provides real-time NIFTY 50, Sensex, and individual stock quote endpoints.
Data sourced from Yahoo Finance (yfinance) with 2-minute caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── In-memory cache ─────────────────────────────────────────────────────────
_cache: dict[str, tuple[dict, datetime]] = {}
CACHE_TTL_SECONDS = 120  # 2 minutes


def _get_cached(key: str) -> Optional[dict]:
    if key in _cache:
        data, ts = _cache[key]
        if datetime.now() - ts < timedelta(seconds=CACHE_TTL_SECONDS):
            return data
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = (data, datetime.now())


def _fetch_yf_quote(ticker: str) -> Optional[dict]:
    """Fetch latest quote for a ticker via yfinance."""
    try:
        import yfinance as yf
        import pandas as pd
        t = yf.Ticker(ticker)
        price = None
        prev_close = None

        # Try fast_info first
        try:
            info = t.fast_info
            price = float(info.last_price) if hasattr(info, 'last_price') and info.last_price else None
            prev_close = float(info.previous_close) if hasattr(info, 'previous_close') and info.previous_close else None
        except Exception:
            pass

        if price is None:
            # Fallback: get from history
            hist = t.history(period="5d")
            if hist is not None and len(hist) >= 1:
                # Handle MultiIndex columns from yfinance v1.2+
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                if "Close" in hist.columns:
                    price = float(hist["Close"].dropna().iloc[-1])
                    if len(hist["Close"].dropna()) >= 2:
                        prev_close = float(hist["Close"].dropna().iloc[-2])

        if price is not None:
            change = price - (prev_close or price)
            change_pct = (change / (prev_close or price)) * 100 if prev_close else 0
            return {
                "price": round(price, 2),
                "prev_close": round(prev_close, 2) if prev_close else None,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            }
    except Exception as e:
        logger.warning(f"yfinance quote failed for {ticker}: {e}")
    return None


@router.get("/market/nifty")
async def get_nifty_live():
    """Return real-time NIFTY 50 and Sensex values."""
    cached = _get_cached("nifty_sensex")
    if cached:
        return cached

    nifty = _fetch_yf_quote("^NSEI")
    sensex = _fetch_yf_quote("^BSESN")

    result = {
        "nifty": nifty or {"price": 22500, "change": 0, "change_pct": 0},
        "sensex": sensex or {"price": 74000, "change": 0, "change_pct": 0},
        "timestamp": datetime.now().isoformat(),
        "live": nifty is not None,
    }
    _set_cache("nifty_sensex", result)
    return result


@router.get("/market/quotes/{stock}")
async def get_stock_quote(stock: str):
    """Return live quote for a single NSE stock."""
    ticker = stock.upper()
    if not ticker.endswith(".NS") and not ticker.startswith("^"):
        ticker = ticker + ".NS"

    cache_key = f"quote_{ticker}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    quote = _fetch_yf_quote(ticker)
    if quote:
        result = {
            "stock": stock.upper(),
            "ticker": ticker,
            **quote,
            "timestamp": datetime.now().isoformat(),
            "live": True,
        }
        _set_cache(cache_key, result)
        return result

    return {
        "stock": stock.upper(),
        "ticker": ticker,
        "price": None,
        "error": "Could not fetch live data",
        "timestamp": datetime.now().isoformat(),
        "live": False,
    }


@router.get("/market/bulk")
async def get_bulk_quotes():
    """Return live quotes for all tracked stocks (for heatmap)."""
    from app.ingestion.data_ingestion import TRACKED_STOCKS

    cache_key = "bulk_quotes"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    quotes = {}
    for stock, ticker in TRACKED_STOCKS:
        quote = _fetch_yf_quote(ticker)
        if quote:
            quotes[stock] = {**quote, "ticker": ticker}

    # Also get indices
    nifty = _fetch_yf_quote("^NSEI")
    sensex = _fetch_yf_quote("^BSESN")

    result = {
        "quotes": quotes,
        "nifty": nifty or {"price": 0, "change_pct": 0},
        "sensex": sensex or {"price": 0, "change_pct": 0},
        "timestamp": datetime.now().isoformat(),
        "count": len(quotes),
    }
    _set_cache(cache_key, result)
    return result
