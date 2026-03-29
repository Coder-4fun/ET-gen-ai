"""ET Markets — Backtest API Routes"""
from fastapi import APIRouter, BackgroundTasks
from app.schemas import BacktestResponse, BacktestRunRequest, StatusResponse
from app.scoring.backtest_engine import get_backtest_result, get_all_signal_type_backtests

router = APIRouter()

@router.get("/all", response_model=list[BacktestResponse])
async def get_all_backtests():
    return get_all_signal_type_backtests()

@router.get("/{signal_type}", response_model=BacktestResponse)
async def get_backtest_by_signal(signal_type: str):
    return get_backtest_result(signal_type)

@router.get("/stock/{stock}", response_model=BacktestResponse)
async def get_backtest_by_stock(stock: str):
    # Find most recent signal type for this stock
    from app.state import app_state
    signals = [s for s in app_state.get_signals() if s.get("stock", "").upper() == stock.upper()]
    signal_type = signals[0].get("signal", "VolumeSpike") if signals else "VolumeSpike"
    ticker = signals[0].get("ticker", stock + ".NS") if signals else stock + ".NS"
    return get_backtest_result(signal_type, stock=stock, ticker=ticker)

@router.post("/run", response_model=StatusResponse)
async def run_custom_backtest(req: BacktestRunRequest, background_tasks: BackgroundTasks):
    async def _run():
        get_backtest_result(
            req.signal_type, stock=req.stock,
            ticker=req.stock + ".NS", run_live=True,
            start_date=req.start_date, end_date=req.end_date
        )
    background_tasks.add_task(_run)
    return StatusResponse(success=True, message="Backtest started in background")
