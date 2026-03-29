"""
ET Markets — Alerts API Routes (Enhanced)

Endpoints for:
- Alert configuration (email, SMS, WhatsApp toggles + contacts)
- Alert history
- Test alerts
- Price target alerts (Groww-style)
- Events calendar
- Alert statistics
- Notification preferences
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas import AlertConfigRequest, AlertResponse, StatusResponse
from app.alerts.alert_engine import (
    get_alert_history, get_config, set_config, dispatch_alert, get_alert_stats
)
from app.alerts.price_alert import (
    add_price_alert, get_price_alerts, delete_price_alert,
    toggle_price_alert, check_price_alerts, get_upcoming_events
)
from app.state import app_state

router = APIRouter()


# ─── Alert Config ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[AlertResponse])
async def get_alerts(limit: int = 50):
    return get_alert_history(limit)


@router.get("/config")
async def get_alert_config():
    return get_config()


@router.post("/config", response_model=StatusResponse)
async def update_alert_config(config: AlertConfigRequest):
    set_config(config.model_dump())
    return StatusResponse(success=True, message="Alert configuration updated")


@router.get("/stats")
async def alert_stats():
    """Get alert statistics for dashboard widgets."""
    return get_alert_stats()


@router.post("/test", response_model=StatusResponse)
async def send_test_alert():
    """Send a test alert using the first available signal."""
    signals = app_state.get_signals()
    if not signals:
        return StatusResponse(success=False, message="No signals available for test")
    result = await dispatch_alert(signals[0])
    return StatusResponse(
        success=True,
        message=f"Test alert dispatched via: {result.get('dispatched', [])}",
        data=result,
    )


@router.post("/test/{channel}", response_model=StatusResponse)
async def send_test_channel_alert(channel: str):
    """Send a test alert on a specific channel (email, sms, whatsapp)."""
    signals = app_state.get_signals()
    if not signals:
        return StatusResponse(success=False, message="No signals available for test")

    sig = signals[0]
    config = get_config()

    if channel == "email":
        if not config.get("email_address"):
            return StatusResponse(success=False, message="No email address configured")
        from app.alerts.email_sender import send_email_alert
        ok = await send_email_alert(sig, config["email_address"])
        return StatusResponse(success=ok, message=f"Email test {'sent' if ok else 'failed'}")

    elif channel == "sms":
        if not config.get("sms_number"):
            return StatusResponse(success=False, message="No SMS number configured")
        from app.alerts.sms_sender import send_sms_alert, format_sms_alert
        msg = format_sms_alert(sig)
        ok = await send_sms_alert(msg, config["sms_number"])
        return StatusResponse(success=ok, message=f"SMS test {'sent' if ok else 'failed'}")

    elif channel == "whatsapp":
        if not config.get("whatsapp_number"):
            return StatusResponse(success=False, message="No WhatsApp number configured")
        from app.alerts.whatsapp_sender import send_whatsapp_alert
        from app.alerts.alert_engine import format_whatsapp_message
        msg = format_whatsapp_message(sig)
        ok = await send_whatsapp_alert(msg, config["whatsapp_number"])
        return StatusResponse(success=ok, message=f"WhatsApp test {'sent' if ok else 'failed'}")

    return StatusResponse(success=False, message=f"Unknown channel: {channel}")


# ─── Price Target Alerts (Groww-style) ────────────────────────────────────────

class PriceAlertRequest(BaseModel):
    stock: str
    ticker: str
    target_price: float = Field(gt=0)
    direction: str = "above"  # "above" or "below"
    notify_email: bool = True
    notify_sms: bool = False
    notify_push: bool = True


@router.post("/price", response_model=StatusResponse)
async def create_price_alert(req: PriceAlertRequest):
    """Create a Groww-style price target alert."""
    alert = add_price_alert(
        stock=req.stock,
        ticker=req.ticker,
        target_price=req.target_price,
        direction=req.direction,
        notify_email=req.notify_email,
        notify_sms=req.notify_sms,
        notify_push=req.notify_push,
    )
    return StatusResponse(success=True, message=f"Price alert set for {req.stock}", data=alert)


@router.get("/price")
async def list_price_alerts(stock: Optional[str] = None, active_only: bool = True):
    """List all price target alerts."""
    return get_price_alerts(stock=stock, active_only=active_only)


@router.delete("/price/{alert_id}", response_model=StatusResponse)
async def remove_price_alert(alert_id: int):
    ok = delete_price_alert(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Price alert not found")
    return StatusResponse(success=True, message="Price alert deleted")


@router.post("/price/{alert_id}/toggle", response_model=StatusResponse)
async def toggle_alert(alert_id: int):
    alert = toggle_price_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    status = "activated" if alert["active"] else "paused"
    return StatusResponse(success=True, message=f"Price alert {status}", data=alert)


@router.post("/price/check", response_model=StatusResponse)
async def trigger_price_check():
    """Manually check all price alerts against current prices."""
    triggered = await check_price_alerts()
    return StatusResponse(
        success=True,
        message=f"{len(triggered)} price alerts triggered",
        data=triggered,
    )


# ─── Events Calendar (Groww-style) ───────────────────────────────────────────

@router.get("/events")
async def get_events(
    event_type: Optional[str] = None,
    stock: Optional[str] = None,
    watchlist_only: bool = False,
):
    """Get upcoming corporate events (earnings, dividends, splits, etc.)."""
    return {
        "events": get_upcoming_events(
            filter_type=event_type,
            filter_stock=stock,
            watchlist_only=watchlist_only,
        ),
        "types": ["Earnings", "Dividend", "Stock Split", "Bonus", "Rights Issue", "Buyback"],
    }


# ─── Market Movers ───────────────────────────────────────────────────────────

@router.get("/movers")
async def get_market_movers():
    """Get top gainers and losers (Groww-style market movers)."""
    import random

    NIFTY_STOCKS = [
        ("Reliance Industries", "RELIANCE.NS", "Energy"),
        ("HDFC Bank", "HDFCBANK.NS", "Banking"),
        ("Infosys", "INFY.NS", "IT"),
        ("Tata Motors", "TATAMOTORS.NS", "Auto"),
        ("Bajaj Finance", "BAJFINANCE.NS", "NBFC"),
        ("ICICI Bank", "ICICIBANK.NS", "Banking"),
        ("TCS", "TCS.NS", "IT"),
        ("Hindustan Unilever", "HINDUNILVR.NS", "FMCG"),
        ("Kotak Bank", "KOTAKBANK.NS", "Banking"),
        ("Axis Bank", "AXISBANK.NS", "Banking"),
        ("Sun Pharma", "SUNPHARMA.NS", "Pharma"),
        ("Bharti Airtel", "BHARTIARTL.NS", "Telecom"),
        ("Maruti Suzuki", "MARUTI.NS", "Auto"),
        ("Wipro", "WIPRO.NS", "IT"),
        ("Asian Paints", "ASIANPAINT.NS", "Consumer"),
        ("Adani Ports", "ADANIPORTS.NS", "Infrastructure"),
        ("ONGC", "ONGC.NS", "Energy"),
        ("Titan Company", "TITAN.NS", "Consumer"),
        ("Power Grid", "POWERGRID.NS", "Utilities"),
        ("NTPC", "NTPC.NS", "Power"),
    ]

    rng = random.Random(42)  # Deterministic within session
    movers = []
    for name, ticker, sector in NIFTY_STOCKS:
        base_price = rng.uniform(200, 5000)
        change = round(rng.uniform(-6.0, 6.5), 2)
        movers.append({
            "stock": name,
            "ticker": ticker,
            "sector": sector,
            "price": round(base_price, 2),
            "change_pct": change,
            "change_abs": round(base_price * change / 100, 2),
            "volume": f"{rng.uniform(1, 50):.1f}M",
        })

    movers.sort(key=lambda x: x["change_pct"], reverse=True)

    return {
        "gainers": movers[:5],
        "losers": list(reversed(movers[-5:])),
        "most_active": sorted(movers, key=lambda x: float(x["volume"].replace("M", "")), reverse=True)[:5],
    }
