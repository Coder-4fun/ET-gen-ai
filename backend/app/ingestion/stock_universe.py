"""
ET Markets Intelligence Layer v2 — NSE Stock Universe

Manages the full NSE stock universe with intelligent 3-tier prioritization.
- Tier 1: NIFTY 50 — scanned every 60s
- Tier 2: NIFTY 200 midcaps — scanned every 5 mins
- Tier 3: NIFTY 500 — scanned every 15 mins

Falls back to a built-in universe when NSE API is unavailable.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


# ─── Built-in stock universe (no API needed) ──────────────────────────────────
# Covers NIFTY 50 + key midcaps + popular retail stocks

TIER_1_STOCKS = [
    # NIFTY 50 — scanned every 60s
    {"symbol": "RELIANCE",   "company": "Reliance Industries",   "sector": "Energy",         "market_cap": 1700000},
    {"symbol": "TCS",        "company": "TCS",                   "sector": "IT",             "market_cap": 1350000},
    {"symbol": "HDFCBANK",   "company": "HDFC Bank",             "sector": "Banking",        "market_cap": 1200000},
    {"symbol": "INFY",       "company": "Infosys",               "sector": "IT",             "market_cap": 650000},
    {"symbol": "ICICIBANK",  "company": "ICICI Bank",            "sector": "Banking",        "market_cap": 700000},
    {"symbol": "HINDUNILVR", "company": "HUL",                   "sector": "FMCG",           "market_cap": 560000},
    {"symbol": "SBIN",       "company": "SBI",                   "sector": "Banking",        "market_cap": 580000},
    {"symbol": "BHARTIARTL", "company": "Bharti Airtel",         "sector": "Telecom",        "market_cap": 500000},
    {"symbol": "KOTAKBANK",  "company": "Kotak Mahindra Bank",   "sector": "Banking",        "market_cap": 380000},
    {"symbol": "BAJFINANCE", "company": "Bajaj Finance",         "sector": "NBFC",           "market_cap": 420000},
    {"symbol": "LT",         "company": "L&T",                   "sector": "Infrastructure", "market_cap": 450000},
    {"symbol": "ITC",        "company": "ITC",                   "sector": "FMCG",           "market_cap": 540000},
    {"symbol": "AXISBANK",   "company": "Axis Bank",             "sector": "Banking",        "market_cap": 310000},
    {"symbol": "TATAMOTORS", "company": "Tata Motors",           "sector": "Auto",           "market_cap": 260000},
    {"symbol": "SUNPHARMA",  "company": "Sun Pharma",            "sector": "Pharma",         "market_cap": 340000},
    {"symbol": "MARUTI",     "company": "Maruti Suzuki",         "sector": "Auto",           "market_cap": 330000},
    {"symbol": "TITAN",      "company": "Titan Company",         "sector": "Consumer",       "market_cap": 270000},
    {"symbol": "WIPRO",      "company": "Wipro",                 "sector": "IT",             "market_cap": 240000},
    {"symbol": "ONGC",       "company": "ONGC",                  "sector": "Energy",         "market_cap": 260000},
    {"symbol": "TATASTEEL",  "company": "Tata Steel",            "sector": "Metals",         "market_cap": 180000},
    {"symbol": "POWERGRID",  "company": "Power Grid",            "sector": "Utilities",      "market_cap": 250000},
    {"symbol": "NTPC",       "company": "NTPC",                  "sector": "Energy",         "market_cap": 300000},
    {"symbol": "HCLTECH",    "company": "HCL Technologies",      "sector": "IT",             "market_cap": 350000},
    {"symbol": "ASIANPAINT", "company": "Asian Paints",          "sector": "Consumer",       "market_cap": 250000},
    {"symbol": "NESTLEIND",  "company": "Nestle India",          "sector": "FMCG",           "market_cap": 220000},
    {"symbol": "ULTRACEMCO", "company": "UltraTech Cement",      "sector": "Cement",         "market_cap": 240000},
    {"symbol": "DRREDDY",    "company": "Dr Reddy's Labs",       "sector": "Pharma",         "market_cap": 100000},
    {"symbol": "TECHM",      "company": "Tech Mahindra",         "sector": "IT",             "market_cap": 130000},
    {"symbol": "CIPLA",      "company": "Cipla",                 "sector": "Pharma",         "market_cap": 95000},
    {"symbol": "ADANIPORTS", "company": "Adani Ports",           "sector": "Infrastructure", "market_cap": 240000},
    {"symbol": "GRASIM",     "company": "Grasim Industries",     "sector": "Cement",         "market_cap": 170000},
    {"symbol": "BAJAJ-AUTO", "company": "Bajaj Auto",            "sector": "Auto",           "market_cap": 210000},
    {"symbol": "DIVISLAB",   "company": "Divi's Labs",           "sector": "Pharma",         "market_cap": 120000},
    {"symbol": "JSWSTEEL",   "company": "JSW Steel",             "sector": "Metals",         "market_cap": 170000},
    {"symbol": "HEROMOTOCO", "company": "Hero MotoCorp",         "sector": "Auto",           "market_cap": 100000},
    {"symbol": "EICHERMOT",  "company": "Eicher Motors",         "sector": "Auto",           "market_cap": 100000},
    {"symbol": "COALINDIA",  "company": "Coal India",            "sector": "Mining",         "market_cap": 240000},
    {"symbol": "BRITANNIA",  "company": "Britannia",             "sector": "FMCG",           "market_cap": 120000},
    {"symbol": "TATACONSUM", "company": "Tata Consumer",         "sector": "FMCG",           "market_cap": 95000},
    {"symbol": "APOLLOHOSP", "company": "Apollo Hospitals",      "sector": "Healthcare",     "market_cap": 85000},
    {"symbol": "HINDALCO",   "company": "Hindalco",              "sector": "Metals",         "market_cap": 130000},
    {"symbol": "BPCL",       "company": "BPCL",                  "sector": "Energy",         "market_cap": 110000},
    {"symbol": "INDUSINDBK", "company": "IndusInd Bank",         "sector": "Banking",        "market_cap": 95000},
    {"symbol": "M&M",        "company": "Mahindra & Mahindra",   "sector": "Auto",           "market_cap": 300000},
    {"symbol": "BAJAJFINSV", "company": "Bajaj Finserv",         "sector": "NBFC",           "market_cap": 270000},
    {"symbol": "SHRIRAMFIN", "company": "Shriram Finance",       "sector": "NBFC",           "market_cap": 90000},
    {"symbol": "TRENT",      "company": "Trent",                 "sector": "Retail",         "market_cap": 180000},
    {"symbol": "ADANIENT",   "company": "Adani Enterprises",     "sector": "Conglomerate",   "market_cap": 300000},
    {"symbol": "BEL",        "company": "Bharat Electronics",    "sector": "Defence",        "market_cap": 170000},
    {"symbol": "HAL",        "company": "HAL",                   "sector": "Defence",        "market_cap": 280000},
]

TIER_2_STOCKS = [
    # NIFTY Next 50 / MidCap — scanned every 5 mins
    {"symbol": "ZOMATO",     "company": "Zomato",                "sector": "Consumer Services", "market_cap": 170000},
    {"symbol": "PAYTM",      "company": "One97 (Paytm)",         "sector": "Fintech",        "market_cap": 30000},
    {"symbol": "IRCTC",      "company": "IRCTC",                 "sector": "Consumer Services", "market_cap": 60000},
    {"symbol": "DLF",        "company": "DLF",                   "sector": "Real Estate",    "market_cap": 130000},
    {"symbol": "SIEMENS",    "company": "Siemens",               "sector": "Capital Goods",  "market_cap": 150000},
    {"symbol": "ABB",        "company": "ABB India",             "sector": "Capital Goods",  "market_cap": 130000},
    {"symbol": "GODREJPROP", "company": "Godrej Properties",     "sector": "Real Estate",    "market_cap": 50000},
    {"symbol": "PIIND",      "company": "PI Industries",         "sector": "Chemicals",      "market_cap": 45000},
    {"symbol": "MPHASIS",    "company": "MPhasis",               "sector": "IT",             "market_cap": 40000},
    {"symbol": "COLPAL",     "company": "Colgate-Palmolive",     "sector": "FMCG",           "market_cap": 70000},
    {"symbol": "VOLTAS",     "company": "Voltas",                "sector": "Consumer Durables", "market_cap": 35000},
    {"symbol": "TATAPOWER",  "company": "Tata Power",            "sector": "Energy",         "market_cap": 100000},
    {"symbol": "CUMMINSIND", "company": "Cummins India",         "sector": "Capital Goods",  "market_cap": 80000},
    {"symbol": "BHEL",       "company": "BHEL",                  "sector": "Capital Goods",  "market_cap": 90000},
    {"symbol": "IOC",        "company": "Indian Oil",            "sector": "Energy",         "market_cap": 195000},
    {"symbol": "MUTHOOTFIN", "company": "Muthoot Finance",       "sector": "NBFC",           "market_cap": 65000},
    {"symbol": "INDUSTOWER", "company": "Indus Towers",          "sector": "Telecom",        "market_cap": 85000},
    {"symbol": "AUROPHARMA", "company": "Aurobindo Pharma",      "sector": "Pharma",         "market_cap": 60000},
    {"symbol": "HAVELLS",    "company": "Havells India",         "sector": "Consumer Durables", "market_cap": 90000},
    {"symbol": "DMART",      "company": "Avenue Supermarts",     "sector": "Retail",         "market_cap": 280000},
    {"symbol": "NAUKRI",     "company": "Info Edge",             "sector": "Internet",       "market_cap": 70000},
    {"symbol": "POLICYBZR",  "company": "PB Fintech",           "sector": "Fintech",        "market_cap": 55000},
    {"symbol": "VEDL",       "company": "Vedanta",               "sector": "Metals",         "market_cap": 130000},
    {"symbol": "GAIL",       "company": "GAIL India",            "sector": "Energy",         "market_cap": 120000},
    {"symbol": "PETRONET",   "company": "Petronet LNG",          "sector": "Energy",         "market_cap": 45000},
    {"symbol": "NMDC",       "company": "NMDC",                  "sector": "Mining",         "market_cap": 60000},
    {"symbol": "SAIL",       "company": "SAIL",                  "sector": "Metals",         "market_cap": 40000},
    {"symbol": "TATACOMM",   "company": "Tata Communications",   "sector": "Telecom",        "market_cap": 45000},
    {"symbol": "PNB",        "company": "Punjab National Bank",  "sector": "Banking",        "market_cap": 100000},
    {"symbol": "BANKBARODA", "company": "Bank of Baroda",        "sector": "Banking",        "market_cap": 100000},
]


class NSEUniverse:
    """
    Manages the full NSE stock universe with intelligent tiered scanning.
    
    Falls back to built-in universe when NSE API is inaccessible.
    Optionally loads live universe from NSE India API and caches in Redis.
    """

    TIER_INTERVALS = {
        1: 60,      # Tier 1: every 60 seconds
        2: 300,     # Tier 2: every 5 minutes
        3: 900,     # Tier 3: every 15 minutes
    }

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._universe: List[dict] = []
        self._loaded = False

    async def load_universe(self):
        """Load stock universe. Tries Redis cache → NSE API → built-in fallback."""
        # Try Redis cache first
        if self.redis:
            try:
                cached = await self.redis.get("nse:universe")
                if cached:
                    self._universe = json.loads(cached)
                    self._loaded = True
                    logger.info(f"📦 Loaded {len(self._universe)} stocks from Redis cache")
                    return
            except Exception:
                pass

        # Try live NSE API
        try:
            live = await self._fetch_from_nse()
            if live:
                self._universe = live
                self._loaded = True
                if self.redis:
                    await self.redis.setex("nse:universe", 86400, json.dumps(live))
                logger.info(f"🌐 Loaded {len(live)} stocks from NSE API")
                return
        except Exception as e:
            logger.warning(f"NSE API fetch failed: {e}")

        # Fallback to built-in universe
        self._universe = self._build_fallback_universe()
        self._loaded = True
        logger.info(f"📋 Using built-in universe: {len(self._universe)} stocks")

    async def _fetch_from_nse(self) -> Optional[List[dict]]:
        """Attempt to fetch NIFTY 500 from NSE India API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Referer": "https://www.nseindia.com",
                        "Accept": "application/json",
                    },
                )
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    result = []
                    for stock in data:
                        if stock.get("symbol") == "NIFTY 500":
                            continue
                        ffmc = stock.get("ffmc", 0) or 0
                        result.append({
                            "symbol": stock["symbol"],
                            "company": stock.get("meta", {}).get("companyName", stock["symbol"]),
                            "sector": stock.get("meta", {}).get("industry", "Unknown"),
                            "market_cap": ffmc,
                            "tier": self._assign_tier_by_cap(ffmc),
                        })
                    return result if result else None
        except Exception:
            pass
        return None

    def _assign_tier_by_cap(self, ffmc: float) -> int:
        """Assign scan tier based on free-float market cap (in Crores)."""
        if ffmc > 50000:
            return 1  # Large Cap (>50,000 Cr)
        if ffmc > 10000:
            return 2  # Mid Cap (>10,000 Cr)
        return 3      # Small Cap

    def _build_fallback_universe(self) -> List[dict]:
        """Build universe from built-in stock lists."""
        universe = []
        for s in TIER_1_STOCKS:
            universe.append({**s, "tier": 1})
        for s in TIER_2_STOCKS:
            universe.append({**s, "tier": 2})
        return universe

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def total_stocks(self) -> int:
        return len(self._universe)

    def get_tier(self, tier: int) -> List[dict]:
        """Get all stocks for a specific scan tier."""
        return [s for s in self._universe if s.get("tier") == tier]

    def get_tier_symbols(self, tier: int) -> List[str]:
        """Get just the ticker symbols for a scan tier."""
        return [s["symbol"] for s in self._universe if s.get("tier") == tier]

    def get_tier_tuples(self, tier: int) -> List[tuple]:
        """Get (stock_name, ticker) tuples for a scan tier, compatible with TRACKED_STOCKS format."""
        return [
            (s["symbol"], f"{s['symbol']}.NS")
            for s in self._universe if s.get("tier") == tier
        ]

    def get_sector_stocks(self, sector: str) -> List[str]:
        """Get all stocks in a sector for sector-rotation signals."""
        return [
            s["symbol"] for s in self._universe
            if sector.lower() in s.get("sector", "").lower()
        ]

    def get_all_sectors(self) -> List[str]:
        """Get unique sector list."""
        return sorted(set(s.get("sector", "Unknown") for s in self._universe))

    def get_stats(self) -> dict:
        """Get universe statistics."""
        from collections import Counter
        tier_counts = Counter(s.get("tier", 0) for s in self._universe)
        sector_counts = Counter(s.get("sector", "Unknown") for s in self._universe)
        return {
            "total": len(self._universe),
            "tiers": dict(tier_counts),
            "sectors": dict(sector_counts),
            "intervals": self.TIER_INTERVALS,
        }


# ─── Module singleton ────────────────────────────────────────────────────────
_universe: Optional[NSEUniverse] = None


async def get_universe(redis_client=None) -> NSEUniverse:
    """Get or create the singleton universe instance."""
    global _universe
    if _universe is None or not _universe.is_loaded:
        _universe = NSEUniverse(redis_client)
        await _universe.load_universe()
    return _universe
