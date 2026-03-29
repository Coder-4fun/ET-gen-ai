"""
ET Markets Intelligence Layer v2 — Portfolio Broker Sync

Multi-broker portfolio aggregation service.
Supports: Zerodha Kite, Angel One (Groww, ICICI stub-ready).

In hackathon mode: returns realistic mock portfolio data.
In production: connects to actual broker APIs.
"""

import os
import json
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_DATA", "true").lower() == "true"


# ─── Abstract Broker Adapter ─────────────────────────────────────────────────

class BrokerAdapter(ABC):
    @abstractmethod
    async def get_holdings(self) -> list[dict]:
        ...

    @abstractmethod
    async def get_positions(self) -> list[dict]:
        ...


# ─── Zerodha Kite Connect ────────────────────────────────────────────────────

class ZerodhaAdapter(BrokerAdapter):
    """Zerodha Kite Connect API integration."""

    BASE_URL = "https://api.kite.trade"

    def __init__(self, api_key: str, access_token: str):
        self.headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {api_key}:{access_token}",
        }

    async def get_holdings(self) -> list[dict]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.BASE_URL}/portfolio/holdings",
                    headers=self.headers,
                )
                r.raise_for_status()
                holdings = r.json()["data"]
                return [
                    {
                        "symbol": h["tradingsymbol"],
                        "exchange": h["exchange"],
                        "qty": h["quantity"],
                        "avg_price": h["average_price"],
                        "current_price": h["last_price"],
                        "current_value": h["quantity"] * h["last_price"],
                        "pnl": h["pnl"],
                        "pnl_pct": (h["pnl"] / (h["quantity"] * h["average_price"])) * 100
                        if h["quantity"] * h["average_price"] > 0 else 0,
                        "broker": "zerodha",
                    }
                    for h in holdings
                ]
        except Exception as e:
            logger.error(f"Zerodha holdings fetch failed: {e}")
            return []

    async def get_positions(self) -> list[dict]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.BASE_URL}/portfolio/positions",
                    headers=self.headers,
                )
                r.raise_for_status()
                return r.json()["data"]["net"]
        except Exception as e:
            logger.error(f"Zerodha positions fetch failed: {e}")
            return []


# ─── Angel One SmartAPI ──────────────────────────────────────────────────────

class AngelOneAdapter(BrokerAdapter):
    """Angel One SmartAPI integration."""

    BASE_URL = "https://apiconnect.angelbroking.com"

    def __init__(self, api_key: str, auth_token: str, client_code: str):
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-ClientCode": client_code,
            "X-PrivateKey": api_key,
            "X-SourceID": "WEB",
        }

    async def get_holdings(self) -> list[dict]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.BASE_URL}/rest/secure/angelbroking/portfolio/v1/getHolding",
                    headers=self.headers,
                )
                data = r.json().get("data", [])
                return [
                    {
                        "symbol": h["tradingsymbol"],
                        "exchange": h["exchange"],
                        "qty": h["quantity"],
                        "avg_price": h["averageprice"],
                        "current_price": h["ltp"],
                        "current_value": h["quantity"] * h["ltp"],
                        "pnl": (h["ltp"] - h["averageprice"]) * h["quantity"],
                        "pnl_pct": ((h["ltp"] - h["averageprice"]) / h["averageprice"]) * 100
                        if h["averageprice"] > 0 else 0,
                        "broker": "angelone",
                    }
                    for h in (data or [])
                ]
        except Exception as e:
            logger.error(f"Angel One holdings fetch failed: {e}")
            return []

    async def get_positions(self) -> list[dict]:
        return []


# ─── Mock Broker (Hackathon mode) ────────────────────────────────────────────

MOCK_HOLDINGS = [
    {"symbol": "RELIANCE",   "qty": 25,  "avg_price": 2380.0, "sector": "Energy"},
    {"symbol": "HDFCBANK",   "qty": 40,  "avg_price": 1590.0, "sector": "Banking"},
    {"symbol": "INFY",       "qty": 60,  "avg_price": 1420.0, "sector": "IT"},
    {"symbol": "TCS",        "qty": 15,  "avg_price": 3650.0, "sector": "IT"},
    {"symbol": "ICICIBANK",  "qty": 50,  "avg_price": 945.0,  "sector": "Banking"},
    {"symbol": "BAJFINANCE", "qty": 12,  "avg_price": 6890.0, "sector": "NBFC"},
    {"symbol": "TATAMOTORS", "qty": 80,  "avg_price": 620.0,  "sector": "Auto"},
    {"symbol": "SUNPHARMA",  "qty": 35,  "avg_price": 1180.0, "sector": "Pharma"},
    {"symbol": "LT",         "qty": 20,  "avg_price": 3250.0, "sector": "Infrastructure"},
    {"symbol": "WIPRO",      "qty": 100, "avg_price": 420.0,  "sector": "IT"},
    {"symbol": "TITAN",      "qty": 18,  "avg_price": 3100.0, "sector": "Consumer"},
    {"symbol": "MARUTI",     "qty": 5,   "avg_price": 10500.0,"sector": "Auto"},
    {"symbol": "KOTAKBANK",  "qty": 30,  "avg_price": 1780.0, "sector": "Banking"},
    {"symbol": "ASIANPAINT", "qty": 22,  "avg_price": 2850.0, "sector": "Consumer"},
    {"symbol": "ITC",        "qty": 150, "avg_price": 410.0,  "sector": "FMCG"},
]


class MockBrokerAdapter(BrokerAdapter):
    """Mock broker for hackathon demo."""

    async def get_holdings(self) -> list[dict]:
        rng = random.Random(datetime.now().strftime("%Y%m%d%H"))
        holdings = []
        for h in MOCK_HOLDINGS:
            drift = rng.uniform(-0.06, 0.08)  # -6% to +8% range
            current_price = round(h["avg_price"] * (1 + drift), 2)
            invested = h["qty"] * h["avg_price"]
            current_val = h["qty"] * current_price
            pnl = current_val - invested
            holdings.append({
                "symbol": h["symbol"],
                "exchange": "NSE",
                "qty": h["qty"],
                "avg_price": h["avg_price"],
                "current_price": current_price,
                "current_value": round(current_val, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl / invested * 100, 2) if invested else 0,
                "sector": h["sector"],
                "broker": "mock",
                "day_change_pct": round(rng.uniform(-2.5, 3.0), 2),
            })
        return holdings

    async def get_positions(self) -> list[dict]:
        return []


# ─── Broker Sync Service ─────────────────────────────────────────────────────

class BrokerSyncService:
    """
    Manages multi-broker portfolio aggregation.
    Supports: Zerodha, Angel One, Mock (hackathon).
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.CACHE_TTL = 300  # 5 minutes

    async def get_portfolio(self, user_id: str = "default") -> dict:
        """Get aggregated portfolio for a user (all connected brokers)."""
        # Check cache
        if self.redis:
            try:
                cached = await self.redis.get(f"portfolio:{user_id}")
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # Get holdings from connected adapter
        adapter = self._get_adapter(user_id)
        holdings = await adapter.get_holdings()

        portfolio = self._aggregate(holdings)

        # Cache result
        if self.redis:
            try:
                await self.redis.setex(
                    f"portfolio:{user_id}",
                    self.CACHE_TTL,
                    json.dumps(portfolio, default=str),
                )
            except Exception:
                pass

        return portfolio

    def _get_adapter(self, user_id: str) -> BrokerAdapter:
        """Get the appropriate broker adapter for a user."""
        # In production, load from DB based on user's broker connections
        zerodha_key = os.getenv("ZERODHA_API_KEY", "")
        zerodha_token = os.getenv("ZERODHA_ACCESS_TOKEN", "")
        if zerodha_key and zerodha_token and zerodha_key != "demo":
            return ZerodhaAdapter(zerodha_key, zerodha_token)

        angel_key = os.getenv("ANGEL_API_KEY", "")
        angel_token = os.getenv("ANGEL_AUTH_TOKEN", "")
        angel_client = os.getenv("ANGEL_CLIENT_CODE", "")
        if angel_key and angel_token and angel_key != "demo":
            return AngelOneAdapter(angel_key, angel_token, angel_client)

        return MockBrokerAdapter()

    def _aggregate(self, holdings: list[dict]) -> dict:
        """Aggregate holdings, compute portfolio-level metrics."""
        if not holdings:
            return {
                "holdings": {},
                "summary": {"total_invested": 0, "total_current": 0, "total_pnl": 0,
                            "total_pnl_pct": 0, "stock_count": 0},
                "concentration": [],
                "sectors": {},
                "timestamp": datetime.now().isoformat(),
            }

        total_invested = sum(h["qty"] * h["avg_price"] for h in holdings)
        total_current = sum(h["current_value"] for h in holdings)
        total_pnl = total_current - total_invested

        # Concentration: each holding as % of portfolio
        sorted_h = sorted(holdings, key=lambda x: x["current_value"], reverse=True)
        concentration = [
            {
                "symbol": h["symbol"],
                "pct": round(h["current_value"] / total_current * 100, 1) if total_current else 0,
                "value": h["current_value"],
            }
            for h in sorted_h[:10]
        ]

        # Sector breakdown
        sector_map = defaultdict(lambda: {"count": 0, "invested": 0, "current": 0, "pnl": 0})
        for h in holdings:
            sector = h.get("sector", "Unknown")
            sector_map[sector]["count"] += 1
            sector_map[sector]["invested"] += h["qty"] * h["avg_price"]
            sector_map[sector]["current"] += h["current_value"]
            sector_map[sector]["pnl"] += h.get("pnl", 0)

        sectors = {}
        for sector, data in sector_map.items():
            sectors[sector] = {
                **data,
                "pnl_pct": round(data["pnl"] / data["invested"] * 100, 2) if data["invested"] else 0,
                "weight_pct": round(data["current"] / total_current * 100, 1) if total_current else 0,
            }

        # Top gainer and loser
        top_gainer = max(holdings, key=lambda h: h.get("pnl_pct", 0))
        top_loser = min(holdings, key=lambda h: h.get("pnl_pct", 0))

        return {
            "holdings": {h["symbol"]: h for h in holdings},
            "holdings_list": sorted_h,
            "summary": {
                "total_invested": round(total_invested, 2),
                "total_current": round(total_current, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl / total_invested * 100, 2) if total_invested else 0,
                "stock_count": len(holdings),
                "top_gainer": {"symbol": top_gainer["symbol"], "pnl_pct": top_gainer.get("pnl_pct", 0)},
                "top_loser": {"symbol": top_loser["symbol"], "pnl_pct": top_loser.get("pnl_pct", 0)},
            },
            "concentration": concentration,
            "sectors": sectors,
            "brokers": list(set(h.get("broker", "unknown") for h in holdings)),
            "timestamp": datetime.now().isoformat(),
        }


# ─── Module singleton ────────────────────────────────────────────────────────
_service: Optional[BrokerSyncService] = None


def get_broker_service(redis_client=None) -> BrokerSyncService:
    global _service
    if _service is None:
        _service = BrokerSyncService(redis_client)
    return _service
