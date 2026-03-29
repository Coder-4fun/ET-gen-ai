"""
ET Markets Intelligence Layer — SendGrid Email Alert Sender

Sends formatted HTML email alerts via SendGrid API.
Falls back gracefully when API key is not configured.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d0f14; color: #e2e8f0; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 32px auto; background: #1a1d27; border-radius: 16px; overflow: hidden; border: 1px solid #2d3748; }}
    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px 32px; }}
    .header h1 {{ margin: 0; font-size: 20px; color: white; }}
    .header p {{ margin: 4px 0 0; color: rgba(255,255,255,0.8); font-size: 13px; }}
    .body {{ padding: 32px; }}
    .signal-card {{ background: #0d0f14; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 4px solid {risk_color}; }}
    .stock-name {{ font-size: 24px; font-weight: 700; color: #f7fafc; }}
    .signal-type {{ font-size: 14px; color: #a0aec0; margin-top: 4px; }}
    .confidence-bar {{ background: #2d3748; border-radius: 4px; height: 8px; margin: 12px 0; overflow: hidden; }}
    .confidence-fill {{ height: 100%; background: {risk_color}; border-radius: 4px; width: {confidence_pct}%; }}
    .explanation {{ font-size: 15px; line-height: 1.6; color: #cbd5e0; margin-top: 12px; }}
    .stats {{ display: flex; gap: 16px; margin-top: 16px; }}
    .stat {{ background: #1a1d27; border-radius: 8px; padding: 10px 14px; flex: 1; }}
    .stat-label {{ font-size: 11px; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stat-value {{ font-size: 18px; font-weight: 700; color: #f7fafc; margin-top: 2px; }}
    .footer {{ padding: 16px 32px; border-top: 1px solid #2d3748; font-size: 12px; color: #4a5568; text-align: center; }}
    .risk-badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; background: {risk_bg}; color: {risk_color}; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔔 ET Markets Signal Alert</h1>
      <p>{timestamp}</p>
    </div>
    <div class="body">
      <div class="signal-card">
        <div class="stock-name">{stock}</div>
        <div class="signal-type">{signal_type} &nbsp;<span class="risk-badge">{risk} Risk</span></div>
        <div class="confidence-bar"><div class="confidence-fill"></div></div>
        <div style="font-size:13px;color:#718096;">Confidence: <strong style="color:{risk_color}">{confidence_pct}%</strong></div>
        <div class="explanation">{explanation}</div>
        <div class="stats">
          <div class="stat">
            <div class="stat-label">Backtest Win Rate</div>
            <div class="stat-value">{win_rate}%</div>
          </div>
          <div class="stat">
            <div class="stat-label">Signal Strength</div>
            <div class="stat-value">{"★" * strength}{"☆" * (5 - strength)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Source</div>
            <div class="stat-value" style="font-size:14px">{source}</div>
          </div>
        </div>
      </div>
      <p style="font-size:13px;color:#4a5568;margin-top:16px;">
        ⚠️ This is an AI-generated signal for informational purposes only. 
        Not SEBI-registered investment advice. Please do your own research.
      </p>
    </div>
    <div class="footer">ET Markets Intelligence Layer · AI-powered market signals for Indian retail investors</div>
  </div>
</body>
</html>
"""


async def send_email_alert(signal: dict, to_email: str) -> bool:
    """
    Send an HTML email alert via SendGrid.
    Returns True if sent successfully, False otherwise.
    """
    api_key = os.getenv("SENDGRID_API_KEY", "demo")
    if api_key == "demo" or not api_key:
        logger.info(f"[MOCK] Email alert would be sent to {to_email} for {signal.get('stock')}")
        return True  # Mock success

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        risk = signal.get("risk", "Medium")
        risk_color = {"High": "#fc8181", "Medium": "#f6ad55", "Low": "#68d391"}.get(risk, "#a0aec0")
        risk_bg = {"High": "#2d1b1b", "Medium": "#2d2010", "Low": "#1b2d1e"}.get(risk, "#1a1d27")
        confidence_pct = round(signal.get("confidence", 0.7) * 100)
        win_rate = round((signal.get("backtest_win_rate", 0.6)) * 100)
        strength = signal.get("strength", 3)

        html = EMAIL_TEMPLATE.format(
            stock=signal.get("stock", "UNKNOWN"),
            signal_type=signal.get("signal", "Signal"),
            risk=risk,
            risk_color=risk_color,
            risk_bg=risk_bg,
            confidence_pct=confidence_pct,
            explanation=signal.get("explanation", "A market signal has been detected."),
            win_rate=win_rate,
            strength=min(5, max(1, strength)),
            source=signal.get("source", "AI"),
            timestamp=signal.get("timestamp", "")[:19].replace("T", " "),
        )

        message = Mail(
            from_email=os.getenv("ALERT_FROM_EMAIL", "alerts@etmarkets.ai"),
            to_emails=to_email,
            subject=f"🔔 {signal.get('stock')} — {signal.get('signal')} Signal ({confidence_pct}% confidence)",
            html_content=html,
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code in (200, 202)
    except Exception as e:
        logger.error(f"SendGrid email failed: {e}")
        return False
