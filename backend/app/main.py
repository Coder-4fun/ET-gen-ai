"""
ET Markets Intelligence Layer — FastAPI Application Entry Point

This is the main FastAPI application that:
- Registers all API routers
- Sets up CORS for the React frontend
- Manages WebSocket connections for live signal streaming
- Seeds mock data on startup when MOCK_DATA=true
- Runs REAL signal detection pipeline when MOCK_DATA=false
- Runs a background scheduler for periodic signal updates
"""

import asyncio
import json
import os
import random
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Import routers ──────────────────────────────────────────────────────────
from app.api.routes_signals import router as signals_router
from app.api.routes_portfolio import router as portfolio_router
from app.api.routes_backtest import router as backtest_router
from app.api.routes_chat import router as chat_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_options import router as options_router
from app.api.routes_heatmap import router as heatmap_router
from app.api.routes_market import router as market_router
from app.api.routes_alpha import router as alpha_router
from app.api.routes_radar import router as radar_router
from app.api.routes_video import router as video_router
from app.api.routes_watchlist import router as watchlist_router
from app.api.routes_v2 import router as v2_router
from app.database import init_db, get_db
from app.state import app_state

MOCK_MODE = os.getenv("MOCK_DATA", "true").lower() == "true"


# ─── WebSocket Connection Manager ────────────────────────────────────────────
class ConnectionManager:
    """Manages active WebSocket connections for live signal broadcasting."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()
app_state.ws_manager = manager


# ─── Live Signal Detection Cycle ─────────────────────────────────────────────
async def run_live_signal_cycle():
    """
    v2 Real signal detection pipeline:
    1. Fetch live OHLCV data from yfinance for all tracked stocks
    2. Run anomaly detector (Z-score, Bollinger, VWAP, volatility)
    3. Run pattern detector (candlestick recognition)
    4. Run NLP detector on any available news
    5. [v2] Detect market regime from NIFTY data → adjust signal confidence
    6. [v2] Deduplicate + correlate signals (composite signal creation)
    7. Generate AI explanations for top signals
    8. Merge into state & broadcast via WebSocket
    """
    if MOCK_MODE:
        await _simulate_mock_signal()
        return

    from app.ingestion.data_ingestion import TRACKED_STOCKS, fetch_stock_data, fetch_news_articles
    from app.signals.anomaly_detector import detect_anomalies
    from app.signals.pattern_detector import detect_patterns
    from app.signals.signal_detector import batch_detect_signals
    from app.intelligence.explanation_agent import generate_explanation
    from app.signals.regime_detector import get_current_regime, apply_regime_to_signal
    from app.signals.signal_correlator import get_correlator

    logger.info("🔄 Running v2 live signal detection cycle…")
    new_signals = []
    correlator = get_correlator()

    # ── 1. Technical signals from price data ─────────────────────────────
    nifty_df = None
    for stock, ticker in TRACKED_STOCKS:
        try:
            df = fetch_stock_data(ticker, period_days=90)
            if df is not None and len(df) > 20:
                anomalies = detect_anomalies(df, stock, ticker)
                pats = detect_patterns(df, stock, ticker)
                new_signals.extend(anomalies + pats)
                # Use first available large-cap data as proxy for regime
                if nifty_df is None and stock in ("RELIANCE", "HDFCBANK", "TCS"):
                    nifty_df = df
        except Exception as e:
            logger.warning(f"Technical detection failed for {stock}: {e}")

    # ── 2. NLP signals from news ─────────────────────────────────────────
    try:
        articles = fetch_news_articles("NSE India stocks NIFTY", limit=20)
        if articles:
            nlp_signals = batch_detect_signals(articles)
            new_signals.extend(nlp_signals)
    except Exception as e:
        logger.warning(f"NLP signal detection failed: {e}")

    # ── 3. [v2] Detect market regime & adjust signals ────────────────────
    regime = get_current_regime(nifty_df)
    logger.info(f"📊 Market regime: {regime.regime.value} (confidence: {regime.confidence:.0%})")

    regime_adjusted = []
    for sig in new_signals:
        adjusted = apply_regime_to_signal(sig, regime)
        regime_adjusted.append(adjusted)
    new_signals = regime_adjusted

    # ── 4. [v2] Dedup + correlation ──────────────────────────────────────
    processed_signals = []
    for sig in new_signals:
        try:
            result = await correlator.process(sig)
            if result is not None:
                processed_signals.append(result)
        except Exception as e:
            logger.warning(f"Signal correlation failed: {e}")
            processed_signals.append(sig)
    
    dropped = len(new_signals) - len(processed_signals)
    if dropped > 0:
        logger.info(f"🔗 Signal correlator: {dropped} duplicates dropped, {len(processed_signals)} signals kept")
    new_signals = processed_signals

    # ── 5. Generate explanations for top signals ─────────────────────────
    if new_signals:
        new_signals.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        for sig in new_signals[:10]:
            if not sig.get("explanation") or sig.get("is_composite"):
                try:
                    sig["explanation"] = await generate_explanation(sig)
                except Exception:
                    pass

    # ── 6. Merge into state & broadcast ──────────────────────────────────
    if new_signals:
        existing = {}
        for s in app_state.get_signals():
            key = f"{s.get('stock')}_{s.get('signal')}"
            if key not in existing or s.get("confidence", 0) > existing[key].get("confidence", 0):
                existing[key] = s

        for s in new_signals:
            key = f"{s.get('stock')}_{s.get('signal')}"
            if key not in existing or s.get("confidence", 0) >= existing[key].get("confidence", 0):
                existing[key] = s

        all_signals = sorted(existing.values(), key=lambda s: s.get("confidence", 0), reverse=True)
        app_state.mock_data["signals"] = list(all_signals)[:50]

        # Store regime info in app state for API access
        app_state.mock_data["regime"] = {
            "regime": regime.regime.value,
            "confidence": round(regime.confidence, 2),
            "signal_multiplier": regime.signal_multiplier,
            "indicators": regime.key_indicators,
        }

        top = new_signals[0]
        top["live"] = True
        top["timestamp"] = datetime.now().isoformat()
        await manager.broadcast({
            "type": "NEW_SIGNAL",
            "payload": top,
            "ts": datetime.now().isoformat(),
            "total_signals": len(new_signals),
            "regime": regime.regime.value,
        })

        logger.info(
            f"✅ v2 cycle complete: {len(new_signals)} signals "
            f"(regime={regime.regime.value}, top={top.get('stock')} {top.get('confidence', 0):.0%})"
        )
    else:
        logger.info("⚠️ Live cycle: no new signals detected")


async def _simulate_mock_signal():
    """Fallback: broadcast mock signal when in MOCK_DATA=true mode."""
    if not manager.active_connections:
        return

    mock_path = Path(__file__).parent.parent / "mock_data" / "mock_signals.json"
    if mock_path.exists():
        with open(mock_path) as f:
            signals = json.load(f)
        signal = random.choice(signals)
        signal["confidence"] = round(signal["confidence"] + random.uniform(-0.03, 0.03), 2)
        signal["confidence"] = max(0.0, min(1.0, signal["confidence"]))
        signal["timestamp"] = datetime.now().isoformat()
        signal["live"] = True
        await manager.broadcast({
            "type": "NEW_SIGNAL",
            "payload": signal,
            "ts": datetime.now().isoformat()
        })


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    if MOCK_MODE:
        # Seed mock data
        mock_base = Path(__file__).parent.parent / "mock_data"
        for fname in ["mock_signals.json", "mock_portfolio.json", "mock_news.json", "mock_options.json"]:
            fpath = mock_base / fname
            if fpath.exists():
                with open(fpath) as f:
                    key = fname.replace("mock_", "").replace(".json", "")
                    app_state.mock_data[key] = json.load(f)
        print("✅ Mock data loaded")
    else:
        # Seed portfolio from mock (so portfolio view works before user adds real holdings)
        mock_pf = Path(__file__).parent.parent / "mock_data" / "mock_portfolio.json"
        if mock_pf.exists():
            with open(mock_pf) as f:
                app_state.mock_data["portfolio"] = json.load(f)

        # Run initial live ingestion
        print("🔄 Running initial live signal detection…")
        try:
            await run_live_signal_cycle()
        except Exception as e:
            print(f"⚠️ Initial ingestion partially failed: {e}")
        print("✅ Live mode initialized")

    print("✅ Database initialized")

    # Start background scheduler
    scheduler = AsyncIOScheduler()
    if MOCK_MODE:
        scheduler.add_job(run_live_signal_cycle, "interval", seconds=15, id="signal_broadcaster")
        print("✅ Mock signal broadcaster started (every 15s)")
    else:
        # Real-time: run every 60 seconds
        scheduler.add_job(run_live_signal_cycle, "interval", seconds=60, id="live_signal_cycle",
                          max_instances=1, misfire_grace_time=30)
        print("✅ Live signal cycle started (every 60s)")

    # Price alert checker (every 30s)
    async def _check_price_alerts():
        try:
            from app.alerts.price_alert import check_price_alerts
            await check_price_alerts()
        except Exception as e:
            logger.warning(f"Price alert check failed: {e}")

    scheduler.add_job(_check_price_alerts, "interval", seconds=30, id="price_alert_checker")
    print("✅ Price alert checker started (every 30s)")

    scheduler.start()
    app_state.scheduler = scheduler

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    print("👋 ET Markets Intelligence Layer shutting down")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ET Markets Intelligence Layer",
    description="AI-powered financial intelligence system for Indian retail investors — v2",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ─────────────────────────────────────────────────────────
app.include_router(signals_router, prefix="/signals", tags=["Signals"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(backtest_router, prefix="/backtest", tags=["Backtest"])
app.include_router(chat_router, prefix="/chat", tags=["Chatbot"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(options_router, prefix="/options", tags=["Options"])
app.include_router(heatmap_router, tags=["Dashboard"])
app.include_router(market_router, tags=["Market Data"])
app.include_router(alpha_router, tags=["Alpha Score"])
app.include_router(radar_router, tags=["Opportunity Radar"])
app.include_router(video_router, tags=["Market Video"])
app.include_router(watchlist_router, tags=["Watchlist"])
app.include_router(v2_router, tags=["v2 Features"])


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ET Markets Intelligence Layer",
        "version": "2.0.0",
        "status": "running",
        "mode": "LIVE" if not MOCK_MODE else "MOCK",
        "mock_mode": MOCK_MODE,
        "v2_features": ["regime", "correlation", "accuracy", "universe", "broker_sync", "mf_analyzer"],
        "ws_clients": len(manager.active_connections),
        "active_signals": len(app_state.get_signals()),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "mode": "LIVE" if not MOCK_MODE else "MOCK", "timestamp": datetime.now().isoformat()}


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────
@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """
    WebSocket endpoint for live signal streaming.
    Clients connect here to receive real-time signal updates.
    """
    await manager.connect(websocket)
    try:
        # Send connection confirmation with current state
        await websocket.send_json({
            "type": "CONNECTED",
            "message": f"Connected to ET Markets {'LIVE' if not MOCK_MODE else 'MOCK'} signal stream",
            "mode": "LIVE" if not MOCK_MODE else "MOCK",
            "active_signals": len(app_state.get_signals()),
            "ts": datetime.now().isoformat()
        })

        # Keep connection alive, listen for client pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_json({"type": "PONG", "ts": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "HEARTBEAT", "ts": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

