"""
ET Markets Intelligence Layer — SMS Alert Sender

Sends compact SMS alerts via Twilio SMS API.
Falls back gracefully in demo mode (logs alert to console).

Also supports a basic SMTP Email fallback when SendGrid is not configured.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def send_sms_alert(message: str, to_number: str) -> bool:
    """
    Send SMS alert via Twilio SMS API.
    to_number must be in E.164 format: +91XXXXXXXXXX
    Returns True if sent successfully.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "demo")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "demo")
    from_number = os.getenv("TWILIO_SMS_FROM", "")

    if account_sid == "demo" or not account_sid:
        logger.info(f"[MOCK] SMS alert would be sent to {to_number}")
        logger.info(f"[MOCK] SMS Message:\n{message}")
        return True  # Mock success

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        logger.info(f"SMS sent: SID={msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio SMS failed: {e}")
        return False


def format_sms_alert(signal: dict) -> str:
    """Format a compact SMS alert message (max ~160 chars for single SMS)."""
    emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(signal.get("risk", "Medium"), "🔔")
    stock = signal.get("stock", "?")
    sig_type = signal.get("signal", "Signal")
    conf = round(signal.get("confidence", 0) * 100)
    risk = signal.get("risk", "?")

    msg = f"{emoji} {stock}: {sig_type}\nConfidence: {conf}% | Risk: {risk}"

    explanation = signal.get("explanation", "")
    if explanation:
        # Keep total under ~300 chars for reliable delivery
        remaining = 280 - len(msg)
        if remaining > 20:
            msg += f"\n{explanation[:remaining]}"

    msg += "\n-ET Markets AI"
    return msg


def format_price_alert_sms(stock: str, target_price: float, current_price: float, direction: str) -> str:
    """Format a price target alert SMS."""
    arrow = "↑" if direction == "above" else "↓"
    return (
        f"🎯 Price Target Hit!\n"
        f"{stock} is now ₹{current_price:,.2f}\n"
        f"Target: {arrow} ₹{target_price:,.2f}\n"
        f"-ET Markets AI"
    )


# ─── SMTP Email Fallback (no SendGrid needed) ───────────────────────────────

async def send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send email via SMTP (Gmail, Outlook, etc.).
    Uses environment variables for SMTP config.
    Falls back gracefully in demo mode.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)

    if not smtp_host or not smtp_user:
        logger.info(f"[MOCK] SMTP email would be sent to {to_email}: {subject}")
        return True  # Mock success

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f"SMTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP email failed: {e}")
        return False
