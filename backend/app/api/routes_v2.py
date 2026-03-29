"""
ET Markets v2 — New API Routes

Exposes all v2 features:
- Market regime detection
- Signal accuracy stats
- Stock universe info
- Broker portfolio sync
- MF overlap analyzer
- Cache stats
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Query
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["v2"])


# ─── Market Regime ───────────────────────────────────────────────────────────

@router.get("/regime")
async def get_market_regime():
    """Return current detected market regime."""
    from app.state import app_state
    regime = app_state.mock_data.get("regime")
    if regime:
        return {**regime, "timestamp": datetime.now().isoformat()}

    # Compute fresh if not cached
    try:
        from app.ingestion.data_ingestion import fetch_stock_data
        from app.signals.regime_detector import detect_regime
        df = fetch_stock_data("^NSEI", period_days=250)
        if df is None:
            df = fetch_stock_data("RELIANCE.NS", period_days=250)
        if df is not None and len(df) > 30:
            result = detect_regime(df)
            return {
                "regime": result.regime.value,
                "confidence": round(result.confidence, 2),
                "signal_multiplier": result.signal_multiplier,
                "indicators": result.key_indicators,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.warning(f"Regime detection failed: {e}")

    return {
        "regime": "sideways",
        "confidence": 0.3,
        "signal_multiplier": 1.0,
        "indicators": {},
        "timestamp": datetime.now().isoformat(),
    }


# ─── Signal Accuracy ────────────────────────────────────────────────────────

@router.get("/accuracy")
async def get_accuracy_stats():
    """Return signal accuracy statistics."""
    from app.scoring.accuracy_tracker import get_accuracy_tracker
    tracker = get_accuracy_tracker()
    return tracker.get_accuracy_stats()


@router.get("/accuracy/{signal_type}")
async def get_signal_accuracy(signal_type: str):
    """Return accuracy for a specific signal type."""
    from app.scoring.accuracy_tracker import get_accuracy_tracker
    tracker = get_accuracy_tracker()
    return tracker.get_signal_track_record(signal_type)


# ─── Stock Universe ──────────────────────────────────────────────────────────

@router.get("/universe")
async def get_stock_universe():
    """Return stock universe stats and tier info."""
    from app.ingestion.stock_universe import get_universe
    universe = await get_universe()
    return {
        "stats": universe.get_stats(),
        "tier1_count": len(universe.get_tier(1)),
        "tier2_count": len(universe.get_tier(2)),
        "sectors": universe.get_all_sectors(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/universe/tier/{tier}")
async def get_universe_tier(tier: int):
    """Return all stocks for a specific scan tier."""
    from app.ingestion.stock_universe import get_universe
    universe = await get_universe()
    stocks = universe.get_tier(tier)
    return {
        "tier": tier,
        "interval_seconds": universe.TIER_INTERVALS.get(tier, 900),
        "stocks": stocks,
        "count": len(stocks),
    }


@router.get("/universe/sector/{sector}")
async def get_sector_stocks(sector: str):
    """Return all stocks in a sector."""
    from app.ingestion.stock_universe import get_universe
    universe = await get_universe()
    symbols = universe.get_sector_stocks(sector)
    return {"sector": sector, "symbols": symbols, "count": len(symbols)}


# ─── Broker Portfolio Sync ───────────────────────────────────────────────────

@router.get("/portfolio/sync")
async def get_synced_portfolio():
    """Return aggregated portfolio from connected brokers."""
    from app.portfolio.broker_sync import get_broker_service
    service = get_broker_service()
    portfolio = await service.get_portfolio()
    return portfolio


# ─── Mutual Fund Analyzer ───────────────────────────────────────────────────

@router.get("/mf/funds")
async def get_available_mf_funds():
    """Return list of mutual funds available for analysis."""
    from app.scoring.mf_analyzer import get_mf_analyzer
    analyzer = get_mf_analyzer()
    return {"funds": analyzer.get_available_funds()}


@router.get("/mf/analyze")
async def analyze_mf_overlap(
    codes: str = Query(
        "119598,120503,118825",
        description="Comma-separated MF scheme codes"
    )
):
    """Analyze overlap between selected mutual funds."""
    from app.scoring.mf_analyzer import get_mf_analyzer
    analyzer = get_mf_analyzer()
    scheme_codes = [c.strip() for c in codes.split(",") if c.strip()]
    result = await analyzer.analyze_portfolio(scheme_codes)
    return result


# ─── Cache Stats ─────────────────────────────────────────────────────────────

@router.get("/cache/stats")
async def get_cache_stats():
    """Return cache hit/miss statistics."""
    from app.core.cache_strategy import get_cache
    cache = get_cache()
    return cache.get_stats()


# ─── System Health (v2) ─────────────────────────────────────────────────────

@router.get("/v2/health")
async def get_v2_health():
    """Return v2 system health status."""
    from app.state import app_state

    regime = app_state.mock_data.get("regime", {})
    signals = app_state.get_signals()

    return {
        "version": "2.0",
        "status": "healthy",
        "signal_count": len(signals),
        "market_regime": regime.get("regime", "unknown"),
        "features": {
            "regime_detection": True,
            "signal_correlation": True,
            "accuracy_tracking": True,
            "stock_universe": True,
            "broker_sync": True,
            "mf_analyzer": True,
            "cache_strategy": True,
        },
        "timestamp": datetime.now().isoformat(),
    }
