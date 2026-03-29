"""
ET Markets Intelligence Layer — Alert Engine (Enhanced)

Routes high-confidence signals to Email, SMS, WhatsApp, and In-App.

Channels:
- Email: SendGrid or SMTP fallback
- SMS: Twilio SMS (phone alerts)
- WhatsApp: Twilio WhatsApp Business API
- In-App: Always logged + WebSocket broadcast

Trigger rules:
- confidence >= threshold (configurable, default 0.75)
- signal stock is in user's watchlist
- signal stock is in user's portfolio
- High confidence (>=0.85) always alerts

Frequency caps per channel per day.
"""

import logging
from datetime import datetime, date
from typing import Optional
from app.state import app_state

logger = logging.getLogger(__name__)

# ─── In-memory alert log ─────────────────────────────────────────────────────
_alert_log: list[dict] = []
_daily_counts: dict[str, dict] = {}   # { date_str: { channel: count } }

DEFAULT_CONFIG = {
    # ── Channel toggles ──────────────────────────────────────────
    "email_enabled": True,
    "sms_enabled": False,
    "whatsapp_enabled": False,

    # ── Contact info ─────────────────────────────────────────────
    "email_address": None,
    "sms_number": None,           # Phone number for SMS alerts
    "whatsapp_number": None,

    # ── Thresholds ───────────────────────────────────────────────
    "min_confidence": 0.75,

    # ── Notification preferences (Groww-style) ───────────────────
    "notify_signals": True,       # AI signal alerts
    "notify_price_targets": True, # Price target hit alerts
    "notify_portfolio": True,     # Portfolio P&L alerts
    "notify_events": True,        # Corporate events (earnings, dividends)
    "notify_market_movers": False, # Top gainers/losers alerts

    # ── Watchlist ────────────────────────────────────────────────
    "watchlist": [],
    "portfolio_alerts": True,

    # ── Frequency caps ───────────────────────────────────────────
    "max_emails_per_day": 10,
    "max_sms_per_day": 5,
    "max_whatsapp_per_day": 3,

    # ── Quiet hours (don't disturb) ──────────────────────────────
    "quiet_start": "22:00",       # 10 PM
    "quiet_end": "08:00",         # 8 AM
    "quiet_hours_enabled": False,
}


def get_config() -> dict:
    return app_state.alert_configs.get("default", DEFAULT_CONFIG)


def set_config(config: dict):
    app_state.alert_configs["default"] = {**DEFAULT_CONFIG, **config}


def _get_daily_count(channel: str) -> int:
    today = str(date.today())
    return _daily_counts.get(today, {}).get(channel, 0)


def _increment_daily_count(channel: str):
    today = str(date.today())
    if today not in _daily_counts:
        _daily_counts[today] = {}
    _daily_counts[today][channel] = _daily_counts[today].get(channel, 0) + 1


def _is_quiet_hours() -> bool:
    """Check if current time is within quiet hours."""
    config = get_config()
    if not config.get("quiet_hours_enabled", False):
        return False

    try:
        now = datetime.now().strftime("%H:%M")
        start = config.get("quiet_start", "22:00")
        end = config.get("quiet_end", "08:00")

        if start < end:
            return start <= now <= end
        else:
            # Overnight range (e.g., 22:00 to 08:00)
            return now >= start or now <= end
    except Exception:
        return False


def _should_alert(signal: dict, config: dict) -> bool:
    """Determines whether a signal meets alert criteria."""
    confidence = signal.get("confidence", 0)
    stock = signal.get("stock", "")

    # Check notification category
    sig_type = signal.get("signal", "")
    if sig_type == "PriceTargetHit" and not config.get("notify_price_targets", True):
        return False
    elif not config.get("notify_signals", True):
        return False

    # Confidence threshold
    if confidence < config.get("min_confidence", 0.75):
        return False

    # Quiet hours check
    if _is_quiet_hours():
        return False

    # Watchlist check
    watchlist = config.get("watchlist", [])
    if stock in watchlist:
        return True

    # Portfolio check
    if config.get("portfolio_alerts", True):
        portfolio = app_state.get_portfolio()
        holdings = portfolio.get("holdings", []) if isinstance(portfolio, dict) else []
        portfolio_stocks = [h.get("stock") for h in holdings]
        if stock in portfolio_stocks:
            return True

    # High confidence always alerts
    if confidence >= 0.85:
        return True

    return False


def format_whatsapp_message(signal: dict) -> str:
    """Format a compact WhatsApp alert message."""
    emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(signal.get("risk", "Medium"), "🔔")
    msg = (
        f"{emoji} *{signal.get('stock')}* | {signal.get('signal')}\n"
        f"Confidence: {signal.get('confidence', 0):.0%} | Risk: {signal.get('risk')}\n"
    )
    explanation = signal.get("explanation", "")
    if explanation:
        msg += f"\n{explanation[:200]}\n"
    win_rate = signal.get("backtest_win_rate")
    if win_rate:
        msg += f"\n📊 Backtest win rate: {win_rate:.0%}"
    msg += "\n\n_ET Markets Intelligence Layer_"
    return msg


async def dispatch_alert(signal: dict) -> dict:
    """
    Evaluate signal and dispatch alerts to all configured channels.
    Returns dict with dispatch results.
    """
    config = get_config()
    results = {"stock": signal.get("stock"), "signal": signal.get("signal"), "dispatched": []}

    if not _should_alert(signal, config):
        return results

    from app.alerts.email_sender import send_email_alert
    from app.alerts.whatsapp_sender import send_whatsapp_alert
    from app.alerts.sms_sender import send_sms_alert, format_sms_alert, send_smtp_email

    # ── Email ─────────────────────────────────────────────────────────────
    if config.get("email_enabled") and config.get("email_address"):
        max_emails = config.get("max_emails_per_day", 10)
        if _get_daily_count("email") < max_emails:
            # Try SendGrid first, fallback to SMTP
            success = await send_email_alert(signal, config["email_address"])
            if success:
                _increment_daily_count("email")
                results["dispatched"].append("email")
                _log_alert(signal, "email", success)
            logger.info(f"📧 Email alert dispatched for {signal.get('stock')}")

    # ── SMS (Phone Alert) ─────────────────────────────────────────────────
    if config.get("sms_enabled") and config.get("sms_number"):
        max_sms = config.get("max_sms_per_day", 5)
        if _get_daily_count("sms") < max_sms:
            msg = format_sms_alert(signal)
            success = await send_sms_alert(msg, config["sms_number"])
            if success:
                _increment_daily_count("sms")
                results["dispatched"].append("sms")
                _log_alert(signal, "sms", success)
            logger.info(f"📱 SMS alert dispatched for {signal.get('stock')}")

    # ── WhatsApp ──────────────────────────────────────────────────────────
    if config.get("whatsapp_enabled") and config.get("whatsapp_number"):
        max_wa = config.get("max_whatsapp_per_day", 3)
        if _get_daily_count("whatsapp") < max_wa:
            msg = format_whatsapp_message(signal)
            success = await send_whatsapp_alert(msg, config["whatsapp_number"])
            if success:
                _increment_daily_count("whatsapp")
                results["dispatched"].append("whatsapp")
                _log_alert(signal, "whatsapp", success)
            logger.info(f"💬 WhatsApp alert dispatched for {signal.get('stock')}")

    # ── In-app (always) ───────────────────────────────────────────────────
    _log_alert(signal, "in-app", True)
    results["dispatched"].append("in-app")

    return results


def _log_alert(signal: dict, channel: str, delivered: bool):
    """Append to in-memory alert log."""
    _alert_log.append({
        "id": len(_alert_log) + 1,
        "stock": signal.get("stock"),
        "signal_type": signal.get("signal"),
        "confidence": signal.get("confidence"),
        "channel": channel,
        "message": signal.get("explanation", ""),
        "delivered": delivered,
        "sent_at": datetime.now().isoformat(),
    })


def get_alert_history(limit: int = 50) -> list[dict]:
    """Return recent alert history."""
    return list(reversed(_alert_log))[:limit]


def get_alert_stats() -> dict:
    """Return alert statistics for the dashboard."""
    today = str(date.today())
    today_counts = _daily_counts.get(today, {})

    return {
        "total_alerts": len(_alert_log),
        "today_email": today_counts.get("email", 0),
        "today_sms": today_counts.get("sms", 0),
        "today_whatsapp": today_counts.get("whatsapp", 0),
        "today_total": sum(today_counts.values()),
        "channels_active": {
            "email": get_config().get("email_enabled", False),
            "sms": get_config().get("sms_enabled", False),
            "whatsapp": get_config().get("whatsapp_enabled", False),
        },
    }
