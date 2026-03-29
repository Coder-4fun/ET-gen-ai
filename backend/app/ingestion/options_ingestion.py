"""
ET Markets Intelligence Layer — Options Chain Ingestion

Fetches NSE options chain data from NSEpy or unofficial NSE API.
Falls back to mock data in demo mode.
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_options_chain(stock: str = "NIFTY") -> Optional[dict]:
    """Fetch options chain for a stock/index from NSE."""
    mock_mode = os.getenv("MOCK_DATA", "true").lower() == "true"
    if mock_mode:
        from app.state import app_state
        return app_state.get_options()

    try:
        import httpx
        # NSE unofficial API
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={stock}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/",
        }
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            # First hit the main page to get cookies
            await client.get("https://www.nseindia.com", timeout=10)
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return _parse_nse_chain(data, stock)
    except Exception as e:
        logger.warning(f"NSE options fetch failed for {stock}: {e}")

    from app.state import app_state
    return app_state.get_options()


def _parse_nse_chain(data: dict, stock: str) -> dict:
    """Parse NSE API response into our options chain format."""
    records = data.get("records", {})
    underlying = records.get("underlyingValue", 0)
    expiry_dates = records.get("expiryDates", [])
    expiry = expiry_dates[0] if expiry_dates else "N/A"

    chain = []
    for row in records.get("data", [])[:20]:
        ce = row.get("CE", {})
        pe = row.get("PE", {})
        strike = row.get("strikePrice", 0)
        chain.append({
            "strike": strike,
            "ce_oi": ce.get("openInterest", 0),
            "ce_vol": ce.get("totalTradedVolume", 0),
            "ce_iv": ce.get("impliedVolatility", 15.0),
            "ce_ltp": ce.get("lastPrice", 0),
            "pe_oi": pe.get("openInterest", 0),
            "pe_vol": pe.get("totalTradedVolume", 0),
            "pe_iv": pe.get("impliedVolatility", 15.0),
            "pe_ltp": pe.get("lastPrice", 0),
        })

    from app.signals.options_analyzer import compute_pcr, compute_max_pain, compute_iv_skew
    pcr = compute_pcr(chain)
    max_pain = compute_max_pain(chain)
    iv_skew = compute_iv_skew(chain, underlying)

    return {
        "stock": stock,
        "expiry": expiry,
        "spot_price": underlying,
        "pcr": pcr,
        "max_pain": max_pain,
        "iv_skew": iv_skew,
        "signal": "HighPCR" if pcr > 1.2 else ("UnusualCallOI" if pcr < 0.7 else "NeutralPositioning"),
        "timestamp": datetime.now().isoformat(),
        "chain": chain,
    }
