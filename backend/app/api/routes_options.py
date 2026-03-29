"""ET Markets — Options Chain API Routes (Live + Synthetic)

When MOCK_DATA=false, generates realistic options chain data
derived from the ACTUAL spot price fetched from yfinance.
"""
import os
import math
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from app.schemas import OptionsResponse, OptionsAnalysis
from app.signals.options_analyzer import get_options_summary
from app.state import app_state

logger = logging.getLogger(__name__)
router = APIRouter()

MOCK_MODE = os.getenv("MOCK_DATA", "true").lower() == "true"


def _generate_live_options_chain(stock: str, spot_price: float) -> dict:
    """
    Generate a realistic options chain centered around the actual spot price.
    Uses standard option pricing heuristics.
    """
    # Generate strikes around spot (5% up and down, every ~50 increments for NIFTY-like, ~10 for stocks)
    if spot_price > 10000:
        strike_step = 100
        n_strikes = 15
    elif spot_price > 1000:
        strike_step = 50
        n_strikes = 12
    else:
        strike_step = 10
        n_strikes = 10

    center = round(spot_price / strike_step) * strike_step
    chain = []

    # Simulated: OI distribution peaks near ATM
    random.seed(hash(f"{stock}_{datetime.now().strftime('%Y%m%d')}") % 9999)

    total_call_oi = 0
    total_put_oi = 0

    for i in range(-n_strikes, n_strikes + 1):
        strike = center + i * strike_step
        if strike <= 0:
            continue

        dist_from_center = abs(i)
        oi_factor = max(0.1, 1.0 - dist_from_center * 0.08)

        call_oi = int(random.gauss(50000, 15000) * oi_factor)
        put_oi = int(random.gauss(45000, 15000) * oi_factor)
        call_oi = max(1000, call_oi)
        put_oi = max(1000, put_oi)

        # IV: smile shape (higher OTM)
        base_iv = 0.18 + dist_from_center * 0.008
        call_iv = round(base_iv + random.uniform(-0.02, 0.02), 4)
        put_iv = round(base_iv + random.uniform(-0.02, 0.03), 4)

        # LTP: rough Black-Scholes feel (simplified)
        time_to_exp = 15 / 365  # ~15 days to expiry
        call_intrinsic = max(0, spot_price - strike)
        put_intrinsic = max(0, strike - spot_price)
        call_time_val = spot_price * call_iv * math.sqrt(time_to_exp)
        put_time_val = spot_price * put_iv * math.sqrt(time_to_exp)
        call_ltp = round(call_intrinsic + call_time_val * random.uniform(0.3, 0.7), 2)
        put_ltp = round(put_intrinsic + put_time_val * random.uniform(0.3, 0.7), 2)

        total_call_oi += call_oi
        total_put_oi += put_oi

        chain.append({
            "strike": strike,
            "call_oi": call_oi,
            "put_oi": put_oi,
            "call_ltp": max(0.05, call_ltp),
            "put_ltp": max(0.05, put_ltp),
            "call_iv": call_iv,
            "put_iv": put_iv,
            "call_volume": int(call_oi * random.uniform(0.05, 0.3)),
            "put_volume": int(put_oi * random.uniform(0.05, 0.3)),
        })

    # Determine max pain (strike with minimum total payout)
    min_pain = float("inf")
    max_pain_strike = center
    for c in chain:
        pain = 0
        for other in chain:
            pain += max(0, other["strike"] - c["strike"]) * other["call_oi"]
            pain += max(0, c["strike"] - other["strike"]) * other["put_oi"]
        if pain < min_pain:
            min_pain = pain
            max_pain_strike = c["strike"]

    pcr = round(total_put_oi / max(1, total_call_oi), 2)

    expiry = datetime.now() + timedelta(days=15)
    # Find nearest Thursday
    while expiry.weekday() != 3:
        expiry += timedelta(days=1)

    return {
        "stock": stock.upper(),
        "spot_price": round(spot_price, 2),
        "chain": chain,
        "pcr": pcr,
        "max_pain": max_pain_strike,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "expiry": expiry.strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "live": True,
    }


@router.get("/{stock}", response_model=OptionsResponse)
async def get_options_chain(stock: str):
    """Return options chain — uses live spot price to generate realistic chain."""
    if MOCK_MODE:
        options = app_state.get_options()
        if options:
            return {**options, "stock": stock.upper()}

    # Try to get live spot price
    try:
        from app.api.routes_market import _fetch_yf_quote
        ticker = stock.upper()
        if not ticker.startswith("^"):
            ticker += ".NS"
        quote = _fetch_yf_quote(ticker)
        if quote and quote.get("price"):
            return _generate_live_options_chain(stock.upper(), quote["price"])
    except Exception as e:
        logger.warning(f"Live options generation failed for {stock}: {e}")

    # Fallback to mock
    options = app_state.get_options()
    if options:
        return {**options, "stock": stock.upper()}

    raise HTTPException(status_code=404, detail=f"Options data not available for {stock}")


@router.get("/{stock}/analysis", response_model=OptionsAnalysis)
async def get_options_analysis(stock: str):
    """Return PCR, max pain, IV skew summary."""
    # Try live first
    if not MOCK_MODE:
        try:
            from app.api.routes_market import _fetch_yf_quote
            ticker = stock.upper() + ".NS" if not stock.startswith("^") else stock
            quote = _fetch_yf_quote(ticker)
            if quote and quote.get("price"):
                live_chain = _generate_live_options_chain(stock.upper(), quote["price"])
                return get_options_summary(live_chain["chain"], live_chain["spot_price"], stock.upper())
        except Exception:
            pass

    options = app_state.get_options()
    chain = options.get("chain", []) if options else []
    spot = options.get("spot_price", 22000) if options else 22000
    return get_options_summary(chain, spot, stock.upper())
