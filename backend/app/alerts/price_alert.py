"""
ET Markets Intelligence Layer — Price Target Alert Engine

Groww-style price alerts:
- Users set target prices (above/below)
- System checks periodically and fires email/SMS/in-app alerts
- Supports multiple alerts per stock
"""

import logging
import random
from datetime import datetime
from typing import Optional
from app.state import app_state

logger = logging.getLogger(__name__)

# In-memory price alert store
_price_alerts: list[dict] = []
_price_alert_id = 0


def add_price_alert(
    stock: str,
    ticker: str,
    target_price: float,
    direction: str = "above",  # "above" or "below"
    notify_email: bool = True,
    notify_sms: bool = False,
    notify_push: bool = True,
) -> dict:
    """Create a new price target alert."""
    global _price_alert_id
    _price_alert_id += 1
    alert = {
        "id": _price_alert_id,
        "stock": stock,
        "ticker": ticker,
        "target_price": target_price,
        "direction": direction,
        "notify_email": notify_email,
        "notify_sms": notify_sms,
        "notify_push": notify_push,
        "active": True,
        "triggered": False,
        "triggered_at": None,
        "triggered_price": None,
        "created_at": datetime.now().isoformat(),
    }
    _price_alerts.append(alert)
    logger.info(f"Price alert created: {stock} {direction} ₹{target_price}")
    return alert


def get_price_alerts(stock: Optional[str] = None, active_only: bool = True) -> list[dict]:
    """Get all price alerts, optionally filtered."""
    alerts = _price_alerts
    if stock:
        alerts = [a for a in alerts if a["stock"].upper() == stock.upper()]
    if active_only:
        alerts = [a for a in alerts if a["active"]]
    return list(reversed(alerts))


def delete_price_alert(alert_id: int) -> bool:
    """Delete a price alert by ID."""
    for i, a in enumerate(_price_alerts):
        if a["id"] == alert_id:
            _price_alerts.pop(i)
            return True
    return False


def toggle_price_alert(alert_id: int) -> Optional[dict]:
    """Toggle active state of a price alert."""
    for a in _price_alerts:
        if a["id"] == alert_id:
            a["active"] = not a["active"]
            return a
    return None


async def check_price_alerts() -> list[dict]:
    """
    Check all active price alerts against current prices.
    Returns list of triggered alerts.
    """
    triggered = []

    for alert in _price_alerts:
        if not alert["active"] or alert["triggered"]:
            continue

        stock = alert["stock"]
        target = alert["target_price"]
        direction = alert["direction"]

        # Get current price (mock: derive from stock name hash)
        current_price = _get_current_price(stock, alert["ticker"])

        should_trigger = False
        if direction == "above" and current_price >= target:
            should_trigger = True
        elif direction == "below" and current_price <= target:
            should_trigger = True

        if should_trigger:
            alert["triggered"] = True
            alert["triggered_at"] = datetime.now().isoformat()
            alert["triggered_price"] = current_price
            alert["active"] = False

            triggered.append({
                **alert,
                "current_price": current_price,
            })

            logger.info(f"🎯 Price alert triggered: {stock} @ ₹{current_price}")

    # Dispatch notifications for triggered alerts
    for t in triggered:
        await _dispatch_price_alert_notifications(t)

    return triggered


def _get_current_price(stock: str, ticker: str) -> float:
    """Get current price from portfolio or generate deterministic mock."""
    portfolio = app_state.get_portfolio()
    if isinstance(portfolio, dict):
        for h in portfolio.get("holdings", []):
            if h.get("stock") == stock and h.get("current_price"):
                return h["current_price"]

    # Mock price based on stock name hash
    rng = random.Random(sum(ord(c) for c in stock))
    return round(rng.uniform(300, 4500), 2)


async def _dispatch_price_alert_notifications(alert: dict):
    """Send notifications for a triggered price alert."""
    from app.alerts.alert_engine import get_config

    config = get_config()
    stock = alert["stock"]
    target = alert["target_price"]
    current = alert["current_price"]
    direction = alert["direction"]
    arrow = "↑" if direction == "above" else "↓"

    # In-app notification (always)
    if app_state.ws_manager:
        await app_state.ws_manager.broadcast({
            "type": "PRICE_ALERT",
            "payload": {
                "stock": stock,
                "target_price": target,
                "current_price": current,
                "direction": direction,
                "message": f"🎯 {stock} hit ₹{current:,.2f} (target {arrow} ₹{target:,.2f})",
            },
            "ts": datetime.now().isoformat(),
        })

    # Email notification
    if alert.get("notify_email") and config.get("email_address"):
        try:
            from app.alerts.sms_sender import send_smtp_email
            from app.alerts.email_sender import send_email_alert

            price_signal = {
                "stock": stock,
                "signal": "PriceTargetHit",
                "confidence": 1.0,
                "risk": "Medium",
                "strength": 4,
                "source": "PriceAlert",
                "explanation": f"{stock} has reached your price target of ₹{target:,.2f}. "
                               f"Current price: ₹{current:,.2f}.",
                "timestamp": datetime.now().isoformat(),
            }
            await send_email_alert(price_signal, config["email_address"])
        except Exception as e:
            logger.error(f"Price alert email failed: {e}")

    # SMS notification
    if alert.get("notify_sms") and config.get("sms_number"):
        try:
            from app.alerts.sms_sender import send_sms_alert, format_price_alert_sms
            msg = format_price_alert_sms(stock, target, current, direction)
            await send_sms_alert(msg, config["sms_number"])
        except Exception as e:
            logger.error(f"Price alert SMS failed: {e}")


# ─── Mock corporate events (Groww-style) ─────────────────────────────────────

MOCK_EVENTS = [
    {"type": "Earnings", "stock": "Reliance Industries", "ticker": "RELIANCE.NS",
     "date": "2026-04-15", "detail": "Q4 FY26 Results", "impact": "High"},
    {"type": "Dividend", "stock": "HDFC Bank", "ticker": "HDFCBANK.NS",
     "date": "2026-04-10", "detail": "₹19.50 per share", "impact": "Medium"},
    {"type": "Stock Split", "stock": "Infosys", "ticker": "INFY.NS",
     "date": "2026-04-20", "detail": "1:2 stock split", "impact": "High"},
    {"type": "Earnings", "stock": "Tata Motors", "ticker": "TATAMOTORS.NS",
     "date": "2026-04-18", "detail": "Q4 FY26 Results", "impact": "High"},
    {"type": "Bonus", "stock": "Bajaj Finance", "ticker": "BAJFINANCE.NS",
     "date": "2026-04-25", "detail": "1:1 Bonus Issue", "impact": "High"},
    {"type": "Earnings", "stock": "Zomato", "ticker": "ZOMATO.NS",
     "date": "2026-04-22", "detail": "Q4 FY26 Results", "impact": "Medium"},
    {"type": "Dividend", "stock": "ONGC", "ticker": "ONGC.NS",
     "date": "2026-04-12", "detail": "₹6.25 per share", "impact": "Low"},
    {"type": "Rights Issue", "stock": "Adani Ports", "ticker": "ADANIPORTS.NS",
     "date": "2026-05-01", "detail": "1:5 rights issue at ₹650", "impact": "Medium"},
    {"type": "Earnings", "stock": "Maruti Suzuki", "ticker": "MARUTI.NS",
     "date": "2026-04-28", "detail": "Q4 FY26 Results", "impact": "High"},
    {"type": "Dividend", "stock": "Power Grid", "ticker": "POWERGRID.NS",
     "date": "2026-04-30", "detail": "₹4.75 per share", "impact": "Low"},
    {"type": "Earnings", "stock": "ICICI Bank", "ticker": "ICICIBANK.NS",
     "date": "2026-04-20", "detail": "Q4 FY26 Results", "impact": "High"},
    {"type": "Buyback", "stock": "TCS", "ticker": "TCS.NS",
     "date": "2026-04-28", "detail": "₹4,150 per share buyback", "impact": "High"},
]


def get_upcoming_events(
    filter_type: Optional[str] = None,
    filter_stock: Optional[str] = None,
    watchlist_only: bool = False,
) -> list[dict]:
    """Get upcoming corporate events (Groww-style events calendar)."""
    events = list(MOCK_EVENTS)

    if filter_type:
        events = [e for e in events if e["type"].lower() == filter_type.lower()]

    if filter_stock:
        events = [e for e in events if filter_stock.lower() in e["stock"].lower()]

    if watchlist_only:
        # Load watchlist stocks
        try:
            from app.api.routes_watchlist import _load_watchlist
            wl = _load_watchlist()
            wl_stocks = {w["stock"] for w in wl}
            events = [e for e in events if e["stock"] in wl_stocks]
        except Exception:
            pass

    # Sort by date
    events.sort(key=lambda e: e["date"])
    return events
