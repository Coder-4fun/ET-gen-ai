"""
ET Markets Intelligence Layer — Pydantic Schemas

Request/response schemas for all API endpoints.
Uses Pydantic v2 with model_config for ORM compatibility.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Signal Schemas ───────────────────────────────────────────────────────────
class SignalBase(BaseModel):
    stock: str
    ticker: str
    sector: Optional[str] = None
    signal: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk: str                       # High / Medium / Low
    strength: int = Field(ge=1, le=5)
    source: str


class SignalCreate(SignalBase):
    sentiment_score: Optional[float] = None
    headline: Optional[str] = None
    explanation: Optional[str] = None
    pattern: Optional[str] = None
    pcr: Optional[float] = None
    max_pain: Optional[float] = None
    z_score: Optional[float] = None
    volume_ratio: Optional[float] = None
    mention_velocity: Optional[float] = None
    contributing_signals: Optional[list[str]] = None
    backtest_win_rate: Optional[float] = None
    backtest_avg_return: Optional[float] = None


class SignalResponse(SignalCreate):
    id: str
    timestamp: Optional[str] = None
    live: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)


# ─── Portfolio Schemas ────────────────────────────────────────────────────────
class HoldingCreate(BaseModel):
    stock: str
    ticker: str
    sector: Optional[str] = None
    qty: int = Field(gt=0)
    avg_buy_price: float = Field(gt=0)
    buy_date: str                   # YYYY-MM-DD


class HoldingResponse(BaseModel):
    id: str
    stock: str
    ticker: str
    sector: Optional[str] = None
    qty: int
    avg_buy_price: float
    buy_date: str
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    invested_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None
    active_signals: Optional[int] = 0
    sparkline: Optional[list[float]] = None
    model_config = ConfigDict(from_attributes=True)


class PortfolioSummary(BaseModel):
    total_invested: float
    total_current_value: float
    total_pnl: float
    total_pnl_percent: float
    total_day_change: Optional[float] = None
    total_day_change_percent: Optional[float] = None
    top_gainer: Optional[str] = None
    top_loser: Optional[str] = None
    active_signals_count: Optional[int] = 0


class PortfolioResponse(BaseModel):
    holdings: list[HoldingResponse]
    summary: PortfolioSummary


# ─── Alert Schemas ────────────────────────────────────────────────────────────
class AlertConfigRequest(BaseModel):
    # Channel toggles
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False

    # Contact info
    email_address: Optional[str] = None
    sms_number: Optional[str] = None           # Phone number for SMS alerts
    whatsapp_number: Optional[str] = None

    # Thresholds
    min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)

    # Notification preferences (Groww-style categories)
    notify_signals: bool = True                # AI signal alerts
    notify_price_targets: bool = True          # Price target hit alerts
    notify_portfolio: bool = True              # Portfolio P&L alerts
    notify_events: bool = True                 # Corporate events
    notify_market_movers: bool = False         # Top gainers/losers

    # Watchlist & portfolio
    watchlist: Optional[list[str]] = []
    portfolio_alerts: bool = True

    # Frequency caps
    max_emails_per_day: int = 10
    max_sms_per_day: int = 5
    max_whatsapp_per_day: int = 3

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_start: str = "22:00"
    quiet_end: str = "08:00"


class AlertResponse(BaseModel):
    id: int
    stock: str
    signal_type: str
    confidence: float
    channel: str
    message: str
    delivered: bool
    sent_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ─── Chat Schemas ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatMessage(BaseModel):
    role: str       # user / assistant
    content: str
    timestamp: Optional[str] = None


# ─── Backtest Schemas ─────────────────────────────────────────────────────────
class BacktestResponse(BaseModel):
    stock: Optional[str] = None
    signal_type: str
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_signals: int
    backtest_period: str
    equity_curve: Optional[list[dict]] = None
    model_config = ConfigDict(from_attributes=True)


class BacktestRunRequest(BaseModel):
    stock: str
    signal_type: str
    start_date: str = "2023-01-01"
    end_date: str = "2026-01-01"
    hold_days: int = 5
    stop_loss_pct: float = 3.0


# ─── Options Schemas ──────────────────────────────────────────────────────────
class OptionsStrike(BaseModel):
    strike: float
    ce_oi: int
    ce_vol: int
    ce_iv: float
    ce_ltp: float
    pe_oi: int
    pe_vol: int
    pe_iv: float
    pe_ltp: float


class OptionsResponse(BaseModel):
    stock: str
    expiry: str
    spot_price: float
    pcr: float
    max_pain: float
    iv_skew: str
    signal: str
    timestamp: str
    chain: list[OptionsStrike]
    iv_curve: Optional[list[dict]] = None


class OptionsAnalysis(BaseModel):
    stock: str
    pcr: float
    max_pain: float
    iv_skew: str
    signal: str
    signal_bias: str        # Bullish / Bearish / Neutral
    confidence: float
    interpretation: str


# ─── Heatmap Schemas ─────────────────────────────────────────────────────────
class SectorData(BaseModel):
    sector: str
    change_pct: float
    color: str              # hex color based on performance
    signal_count: int
    top_stock: str
    stocks: list[dict]


class HeatmapResponse(BaseModel):
    sectors: list[SectorData]
    timestamp: str
    nifty_change: float
    sensex_change: float


# ─── Generic ──────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    stocks: Optional[list[str]] = None  # None = analyze all tracked stocks
    force_refresh: bool = False


class StatusResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
