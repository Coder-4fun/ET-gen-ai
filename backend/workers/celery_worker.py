"""ET Markets Intelligence Layer — Celery Worker

Periodic tasks:
- Every 5 minutes: Full data ingestion + signal detection cycle
- Every 5 minutes: Alert dispatch for new high-confidence signals
- Every 60 seconds: Price cache refresh (during market hours 9:15–15:30 IST)

Usage:
  celery -A workers.celery_worker worker --loglevel=info
  celery -A workers.celery_worker beat --loglevel=info
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery(
    "etmarkets",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.celery_worker"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
)

# ─── Beat Schedule (periodic tasks) ──────────────────────────────────────────
app.conf.beat_schedule = {
    "ingest-and-detect-signals": {
        "task": "workers.celery_worker.run_ingestion_and_detection",
        "schedule": 300.0,  # Every 5 minutes
    },
    "refresh-prices": {
        "task": "workers.celery_worker.refresh_prices",
        "schedule": 60.0,   # Every 60 seconds
    },
    "dispatch-alerts": {
        "task": "workers.celery_worker.dispatch_pending_alerts",
        "schedule": 120.0,  # Every 2 minutes
    },
}


@app.task(bind=True, max_retries=3)
def run_ingestion_and_detection(self):
    """Full ingestion + signal detection cycle."""
    import asyncio
    try:
        from app.ingestion.data_ingestion import run_full_ingestion_cycle
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        new_signals = loop.run_until_complete(run_full_ingestion_cycle())
        logger.info(f"[Celery] Ingestion complete: {len(new_signals)} signals detected")
        return {"signals_detected": len(new_signals)}
    except Exception as exc:
        logger.error(f"[Celery] Ingestion task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True)
def refresh_prices(self):
    """Refresh live price cache for all tracked stocks."""
    from datetime import datetime, time
    import pytz

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).time()
    market_open = time(9, 15)
    market_close = time(15, 30)

    if not (market_open <= now <= market_close):
        return {"skipped": "Outside market hours"}

    try:
        from app.ingestion.data_ingestion import TRACKED_STOCKS, fetch_stock_data
        refreshed = 0
        for stock, ticker in TRACKED_STOCKS:
            fetch_stock_data(ticker, period_days=1)
            refreshed += 1
        logger.info(f"[Celery] Prices refreshed for {refreshed} stocks")
        return {"refreshed": refreshed}
    except Exception as e:
        logger.error(f"[Celery] Price refresh failed: {e}")
        return {"error": str(e)}


@app.task(bind=True)
def dispatch_pending_alerts(self):
    """Check for high-confidence signals and dispatch alerts."""
    import asyncio
    try:
        from app.state import app_state
        from app.alerts.alert_engine import dispatch_alert
        signals = app_state.get_signals()
        config = {"min_confidence": 0.80}
        high_conf = [s for s in signals if s.get("confidence", 0) >= config["min_confidence"]]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        dispatched = 0
        for signal in high_conf[:3]:  # Cap at 3 per cycle
            result = loop.run_until_complete(dispatch_alert(signal))
            if result.get("dispatched"):
                dispatched += 1

        logger.info(f"[Celery] Alert dispatch: {dispatched} alerts sent")
        return {"dispatched": dispatched}
    except Exception as e:
        logger.error(f"[Celery] Alert dispatch failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    app.start()
