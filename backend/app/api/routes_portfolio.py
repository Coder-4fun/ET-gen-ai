"""ET Markets — Portfolio API Routes"""
import uuid
from fastapi import APIRouter, HTTPException
from app.schemas import HoldingCreate, PortfolioResponse, StatusResponse
from app.portfolio.portfolio_tracker import (
    add_holding, remove_holding, get_portfolio_with_pnl, seed_from_mock, _holdings
)
from app.state import app_state

router = APIRouter()

@router.get("", response_model=PortfolioResponse)
async def get_portfolio():
    if not _holdings:
        mock = app_state.get_portfolio()
        if mock:
            seed_from_mock(mock)
    signals = app_state.get_signals()
    return get_portfolio_with_pnl(signals)

@router.post("/add", response_model=StatusResponse)
async def add_holding_route(holding: HoldingCreate):
    h = add_holding(
        stock=holding.stock.upper(),
        ticker=holding.ticker,
        qty=holding.qty,
        avg_buy_price=holding.avg_buy_price,
        buy_date=holding.buy_date,
        sector=holding.sector,
    )
    return StatusResponse(success=True, message=f"Added {holding.stock}", data=h)

@router.delete("/{stock}", response_model=StatusResponse)
async def remove_holding_route(stock: str):
    ok = remove_holding(stock.upper())
    if not ok:
        raise HTTPException(status_code=404, detail=f"{stock} not found in portfolio")
    return StatusResponse(success=True, message=f"Removed {stock}")

@router.get("/signals", response_model=list)
async def get_portfolio_signals():
    if not _holdings:
        mock = app_state.get_portfolio()
        if mock:
            seed_from_mock(mock)
    portfolio_stocks = list(_holdings.keys())
    return [s for s in app_state.get_signals() if s.get("stock") in portfolio_stocks]
