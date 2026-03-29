"""
ET Markets Intelligence Layer — Data Ingestion

Fetches OHLCV data from Yahoo Finance / Alpha Vantage.
Caches results in-memory for 5 minutes to avoid rate limits.
Falls back to mock data when MOCK_DATA=true.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[pd.DataFrame, datetime]] = {}
CACHE_TTL_MINUTES = 5

TRACKED_STOCKS = [
    # ── NIFTY 50 Tier 1 — verified working with yfinance 1.2.x ──────────
    ("RELIANCE",   "RELIANCE.NS"),
    ("TCS",        "TCS.NS"),
    ("HDFCBANK",   "HDFCBANK.NS"),
    ("INFY",       "INFY.NS"),
    ("ICICIBANK",  "ICICIBANK.NS"),
    ("SBIN",       "SBIN.NS"),
    ("BHARTIARTL", "BHARTIARTL.NS"),
    ("LT",         "LT.NS"),
    ("AXISBANK",   "AXISBANK.NS"),
    ("WIPRO",      "WIPRO.NS"),
    ("HCLTECH",    "HCLTECH.NS"),
    ("ONGC",       "ONGC.NS"),
    ("NTPC",       "NTPC.NS"),
    ("ITC",        "ITC.NS"),
    ("MARUTI",     "MARUTI.NS"),
    ("SUNPHARMA",  "SUNPHARMA.NS"),
    ("IRCTC",      "IRCTC.NS"),
    ("TATAPOWER",  "TATAPOWER.NS"),
    ("ZOMATO",     "ZOMATO.NS"),
    ("TATAMOTORS", "TATAMOTORS.NS"),
    ("BAJFINANCE", "BAJFINANCE.NS"),
    
    # ── Expanding Universe ───────────────────────────────────────────────
    ("HINDUNILVR", "HINDUNILVR.NS"),
    ("KOTAKBANK",  "KOTAKBANK.NS"),
    ("TITAN",      "TITAN.NS"),
    ("ASIANPAINT", "ASIANPAINT.NS"),
    ("M&M",        "M&M.NS"),
    ("ADANIENT",   "ADANIENT.NS"),
    ("BAJAJFINSV", "BAJAJFINSV.NS"),
    ("NESTLEIND",  "NESTLEIND.NS"),
    ("JSWSTEEL",   "JSWSTEEL.NS"),
    ("GRASIM",     "GRASIM.NS"),
    ("INDUSINDBK", "INDUSINDBK.NS"),
    ("TECHM",      "TECHM.NS"),
    ("DLF",        "DLF.NS"),
    ("TATASTEEL",  "TATASTEEL.NS"),
    ("PAYTM",      "PAYTM.NS"),
    ("DMART",      "DMART.NS"),
    ("HAL",        "HAL.NS"),
    ("RECGTD",     "RECLTD.NS"),
    ("PFC",        "PFC.NS"),
    ("JIOFIN",     "JIOFIN.NS")
]


def _make_mock_ohlcv(ticker: str, days: int = 90) -> pd.DataFrame:
    """Generate synthetic OHLCV data for demo mode."""
    import numpy as np
    np.random.seed(hash(ticker) % 999)
    base = {"RELIANCE.NS": 2800, "ZOMATO.NS": 190, "HDFCBANK.NS": 1580,
            "TATAMOTORS.NS": 950, "PAYTM.NS": 450, "INFY.NS": 1700}.get(ticker, 1000)

    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    prices = [base]
    for _ in range(len(dates) - 1):
        prices.append(round(prices[-1] * (1 + np.random.normal(0.0004, 0.015)), 2))

    df = pd.DataFrame({
        "Open":   [p * (1 + np.random.uniform(-0.005, 0.005)) for p in prices],
        "High":   [p * (1 + np.random.uniform(0.002, 0.018)) for p in prices],
        "Low":    [p * (1 - np.random.uniform(0.002, 0.018)) for p in prices],
        "Close":  prices,
        "Volume": [int(np.random.uniform(1e6, 5e6)) for _ in prices],
    }, index=dates)
    return df.round(2)


def fetch_stock_data(ticker: str, period_days: int = 90) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a ticker. Returns cached data if fresh.
    Falls back to synthetic data in mock mode.
    """
    mock_mode = os.getenv("MOCK_DATA", "true").lower() == "true"

    # Check cache
    if ticker in _cache:
        df, ts = _cache[ticker]
        if datetime.now() - ts < timedelta(minutes=CACHE_TTL_MINUTES):
            return df

    if mock_mode:
        df = _make_mock_ohlcv(ticker, days=period_days)
        _cache[ticker] = (df, datetime.now())
        return df

    try:
        import yfinance as yf
        start = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")
        
        raw = yf.Ticker(ticker).history(start=start, auto_adjust=True)

        if raw is not None and not raw.empty and len(raw) > 10:
            # yf.Ticker.history() returns a flat DataFrame without MultiIndex
            required = ["Open", "High", "Low", "Close", "Volume"]
            if all(c in raw.columns for c in required):
                df = raw[required].copy()
                # Ensure timezone-naive index for downstream consistency if needed
                if pd.api.types.is_datetime64tz_dtype(df.index):
                    df.index = df.index.tz_localize(None)
                df = df.dropna()
                _cache[ticker] = (df, datetime.now())
                logger.info(f"Fetched {len(df)} bars for {ticker}")
                return df
            else:
                logger.warning(f"Missing columns for {ticker}: {list(raw.columns)}")
        else:
            logger.warning(f"Empty or tiny data returned for {ticker} by yfinance")

    except Exception as e:
        logger.warning(f"yfinance failed for {ticker}: {e} — using mock data")

    df = _make_mock_ohlcv(ticker, days=period_days)
    _cache[ticker] = (df, datetime.now())
    return df


def fetch_news_articles(query: str = "NSE India stocks", limit: int = 50) -> list[dict]:
    """Fetch news articles from NewsAPI. Returns mock articles in demo mode."""
    from app.state import app_state
    mock_mode = os.getenv("MOCK_DATA", "true").lower() == "true"
    if mock_mode:
        return app_state.get_news()[:limit]

    api_key = os.getenv("NEWSAPI_KEY", "demo")
    if api_key == "demo":
        return app_state.get_news()[:limit]

    try:
        import httpx
        resp = httpx.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "language": "en", "pageSize": limit, "apiKey": api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            return [{"headline": a["title"], "body": a.get("content", ""),
                     "source": a["source"]["name"], "url": a["url"],
                     "published_at": a["publishedAt"]} for a in articles]
    except Exception as e:
        logger.warning(f"NewsAPI failed: {e}")
    return app_state.get_news()[:limit]


async def run_full_ingestion_cycle():
    """Run a complete ingestion + signal detection cycle."""
    from app.signals.anomaly_detector import detect_anomalies
    from app.signals.pattern_detector import detect_patterns
    from app.state import app_state

    new_signals = []
    for stock, ticker in TRACKED_STOCKS:
        try:
            df = fetch_stock_data(ticker)
            if df is not None:
                anomalies = detect_anomalies(df, stock, ticker)
                patterns = detect_patterns(df, stock, ticker)
                new_signals.extend(anomalies + patterns)
        except Exception as e:
            logger.error(f"Ingestion failed for {stock}: {e}")

    if new_signals:
        existing = {s["id"]: s for s in app_state.get_signals()}
        for s in new_signals:
            existing[s["id"]] = s
        app_state.mock_data["signals"] = list(existing.values())
        logger.info(f"Ingestion cycle complete: {len(new_signals)} new signals detected")

    return new_signals
