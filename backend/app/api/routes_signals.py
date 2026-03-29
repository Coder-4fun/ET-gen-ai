"""ET Markets — Signal API Routes (Live + Mock)"""
import os
import logging
from fastapi import APIRouter, BackgroundTasks
from app.state import app_state
from app.schemas import SignalResponse, AnalyzeRequest, StatusResponse
from app.scoring.signal_scoring import rank_signals

logger = logging.getLogger(__name__)
router = APIRouter()

MOCK_MODE = os.getenv("MOCK_DATA", "true").lower() == "true"


@router.get("", response_model=list[SignalResponse])
async def get_signals(limit: int = 50, risk: str = None, sector: str = None):
    signals = app_state.get_signals()

    # If no signals yet in live mode, trigger a quick fetch
    if not signals and not MOCK_MODE:
        try:
            from app.ingestion.data_ingestion import run_full_ingestion_cycle
            await run_full_ingestion_cycle()
            signals = app_state.get_signals()
        except Exception as e:
            logger.warning(f"On-demand ingestion failed: {e}")

    if risk:
        signals = [s for s in signals if s.get("risk", "").lower() == risk.lower()]
    if sector:
        signals = [s for s in signals if s.get("sector", "").lower() == sector.lower()]
    return sorted(signals, key=lambda s: s.get("confidence", 0), reverse=True)[:limit]


@router.get("/top", response_model=list[SignalResponse])
async def get_top_signals(n: int = 10):
    signals = app_state.get_signals()
    if not signals and not MOCK_MODE:
        try:
            from app.ingestion.data_ingestion import run_full_ingestion_cycle
            await run_full_ingestion_cycle()
            signals = app_state.get_signals()
        except Exception:
            pass
    return rank_signals(signals, top_n=n)


@router.get("/history", response_model=list[SignalResponse])
async def get_signal_history(limit: int = 100):
    return app_state.get_signals()[:limit]


@router.get("/{stock}", response_model=list[SignalResponse])
async def get_stock_signals(stock: str):
    return [s for s in app_state.get_signals() if s.get("stock", "").upper() == stock.upper()]


@router.post("/analyze", response_model=StatusResponse)
async def trigger_analysis(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Trigger a fresh signal detection run (runs in background)."""
    async def _run():
        from app.ingestion.data_ingestion import fetch_stock_data
        from app.signals.anomaly_detector import detect_anomalies
        from app.signals.pattern_detector import detect_patterns
        stocks = req.stocks or ["RELIANCE", "ZOMATO", "HDFCBANK", "PAYTM", "TATAMOTORS", "INFY"]
        new_signals = []
        for stock in stocks:
            try:
                ticker = stock + ".NS"
                df = fetch_stock_data(ticker)
                if df is not None and len(df) > 10:
                    sigs = detect_anomalies(df, stock, ticker)
                    pats = detect_patterns(df, stock, ticker)
                    new_signals.extend(sigs + pats)
            except Exception as e:
                logger.warning(f"Analysis failed for {stock}: {e}")

        # Merge into store
        existing = app_state.get_signals()
        merged = {s["id"]: s for s in existing}
        for s in new_signals:
            merged[s["id"]] = s
        app_state.mock_data["signals"] = list(merged.values())

        # Broadcast if WebSocket clients exist
        if new_signals and app_state.ws_manager:
            top = max(new_signals, key=lambda s: s.get("confidence", 0))
            top["live"] = True
            await app_state.ws_manager.broadcast({
                "type": "NEW_SIGNAL",
                "payload": top,
                "ts": __import__("datetime").datetime.now().isoformat(),
            })

    background_tasks.add_task(_run)
    return StatusResponse(success=True, message="Signal detection run triggered in background")
