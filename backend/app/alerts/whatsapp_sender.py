"""
ET Markets Intelligence Layer — Twilio WhatsApp Alert Sender

Sends compact WhatsApp alerts via Twilio WhatsApp Business API.
Falls back gracefully in demo mode.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def send_whatsapp_alert(message: str, to_number: str) -> bool:
    """
    Send WhatsApp alert via Twilio.
    to_number must be in format: +91XXXXXXXXXX (without 'whatsapp:' prefix)
    Returns True if sent successfully.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "demo")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "demo")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if account_sid == "demo" or not account_sid:
        logger.info(f"[MOCK] WhatsApp alert would be sent to {to_number}")
        logger.info(f"[MOCK] Message:\n{message}")
        return True  # Mock success

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Ensure proper 'whatsapp:' prefix
        to_wa = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_wa,
        )
        logger.info(f"WhatsApp sent: SID={msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio WhatsApp failed: {e}")
        return False
