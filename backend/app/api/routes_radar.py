"""
ET Markets — Opportunity Radar
Tracks high-signal corporate events:
  • Bulk / Block deals
  • Insider trades
  • FII / DII daily activity
  • Promoter holding changes
  • Earnings surprises
  • Regulatory filings
"""

import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from app.state import app_state

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Mock corporate event data (realistic Indian markets data)
# ─────────────────────────────────────────────────────────────────────────────

def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


MOCK_RADAR_EVENTS = [
    # Insider / Promoter trades
    {
        "id": "EVT001",
        "type": "PromoterBuy",
        "stock": "Infosys",
        "ticker": "INFY.NS",
        "sector": "IT",
        "headline": "Promoter N.R. Narayana Murthy acquires 2.1% additional stake via open market",
        "detail": "Promoter group increased stake from 12.8% to 14.9%. Historically similar promoter accumulation signals led to 12–18% upside in 90 days.",
        "value": "₹1,240 Cr",
        "signal_strength": 87,
        "date": _days_ago(1),
        "impact": "Bullish",
        "color": "#10b981",
        "icon": "trending-up",
        "historical_success_rate": 78,
        "avg_return_90d": 14.2,
    },
    {
        "id": "EVT002",
        "type": "BulkDeal",
        "stock": "HDFC Bank",
        "ticker": "HDFCBANK.NS",
        "sector": "Banking",
        "headline": "LIC acquires 1.8% stake in HDFC Bank via bulk deal — ₹2,100 Cr transaction",
        "detail": "LIC — India's largest institutional investor — added to its HDFC Bank position. FII confidence combined with domestic institutional buying signals near-term support.",
        "value": "₹2,100 Cr",
        "signal_strength": 82,
        "date": _days_ago(1),
        "impact": "Bullish",
        "color": "#06b6d4",
        "icon": "zap",
        "historical_success_rate": 71,
        "avg_return_90d": 9.8,
    },
    {
        "id": "EVT003",
        "type": "FIIAccumulation",
        "stock": "Reliance Industries",
        "ticker": "RELIANCE.NS",
        "sector": "Energy",
        "headline": "FIIs net buyers of Reliance for 8 consecutive sessions — ₹3,400 Cr inflow",
        "detail": "Foreign Institutional Investors have accumulated ₹3,400 Cr worth of Reliance stock over 8 sessions. Sustained FII buying has historically preceded a 10–15% rally within 60 days.",
        "value": "₹3,400 Cr",
        "signal_strength": 91,
        "date": _days_ago(0),
        "impact": "Strongly Bullish",
        "color": "#a78bfa",
        "icon": "globe",
        "historical_success_rate": 84,
        "avg_return_90d": 12.7,
    },
    {
        "id": "EVT004",
        "type": "EarningsSurprise",
        "stock": "TCS",
        "ticker": "TCS.NS",
        "sector": "IT",
        "headline": "TCS Q4 PAT beats estimates by 8.4% — ₹12,434 Cr vs ₹11,470 Cr expected",
        "detail": "TCS reported Q4 results significantly beating analyst consensus. Revenue growth of 6.1% YoY driven by BFSI and healthcare verticals. Management guided for double-digit growth in FY27.",
        "value": "₹12,434 Cr PAT",
        "signal_strength": 79,
        "date": _days_ago(2),
        "impact": "Bullish",
        "color": "#f59e0b",
        "icon": "bar-chart",
        "historical_success_rate": 68,
        "avg_return_90d": 8.3,
    },
    {
        "id": "EVT005",
        "type": "InsiderTrade",
        "stock": "Bajaj Finance",
        "ticker": "BAJFINANCE.NS",
        "sector": "NBFC",
        "headline": "MD & CEO Rajeev Jain purchases 15,000 shares worth ₹12.3 Cr in open market",
        "detail": "C-suite insider purchases are considered the strongest insider signal. CEO buying at market price signals high conviction in near-term stock performance.",
        "value": "₹12.3 Cr",
        "signal_strength": 88,
        "date": _days_ago(3),
        "impact": "Strongly Bullish",
        "color": "#10b981",
        "icon": "user-check",
        "historical_success_rate": 82,
        "avg_return_90d": 16.1,
    },
    {
        "id": "EVT006",
        "type": "DIIBuying",
        "stock": "L&T",
        "ticker": "LT.NS",
        "sector": "Infrastructure",
        "headline": "Domestic mutual funds accumulate L&T shares — ₹890 Cr net inflow this week",
        "detail": "HDFC MF, SBI MF, and ICICI Pru MF collectively added L&T positions totalling ₹890 Cr. Infrastructure sector getting re-rated on government capex spend acceleration.",
        "value": "₹890 Cr",
        "signal_strength": 74,
        "date": _days_ago(2),
        "impact": "Bullish",
        "color": "#06b6d4",
        "icon": "building",
        "historical_success_rate": 66,
        "avg_return_90d": 7.9,
    },
    {
        "id": "EVT007",
        "type": "RegulatoryApproval",
        "stock": "Sun Pharma",
        "ticker": "SUNPHARMA.NS",
        "sector": "Pharma",
        "headline": "USFDA grants Sun Pharma tentative approval for generic Revlimid — ₹4,000 Cr opportunity",
        "detail": "US FDA approval for lenalidomide 5mg/10mg capsules opens a major generics market. Sun Pharma's US business could see 15–20% jump in revenues from this molecule alone.",
        "value": "₹4,000 Cr TAM",
        "signal_strength": 85,
        "date": _days_ago(4),
        "impact": "Bullish",
        "color": "#a78bfa",
        "icon": "shield-check",
        "historical_success_rate": 73,
        "avg_return_90d": 11.4,
    },
    {
        "id": "EVT008",
        "type": "PromoterBuy",
        "stock": "Asian Paints",
        "ticker": "ASIANPAINT.NS",
        "sector": "Consumer",
        "headline": "Promoter family increases stake by 1.4% — signals confidence in turnaround",
        "detail": "The Dani family increased stake to 53.9% from 52.5%. Promoter buying during a stock's underperformance phase is often a contrarian bullish trigger.",
        "value": "₹640 Cr",
        "signal_strength": 76,
        "date": _days_ago(5),
        "impact": "Bullish",
        "color": "#10b981",
        "icon": "trending-up",
        "historical_success_rate": 69,
        "avg_return_90d": 10.2,
    },
    {
        "id": "EVT009",
        "type": "BlockDeal",
        "stock": "Wipro",
        "ticker": "WIPRO.NS",
        "sector": "IT",
        "headline": "Promoter Azim Premji offloads 1.2% stake — ₹1,800 Cr block deal",
        "detail": "Promoter stake reduction via block deal. While typically viewed cautiously, Premji Invest has historically monetised at peaks and rotated capital. Monitor for follow-on selling.",
        "value": "₹1,800 Cr",
        "signal_strength": 45,
        "date": _days_ago(1),
        "impact": "Cautionary",
        "color": "#f43f5e",
        "icon": "alert-triangle",
        "historical_success_rate": 38,
        "avg_return_90d": -2.1,
    },
    {
        "id": "EVT010",
        "type": "FIIAccumulation",
        "stock": "Kotak Mahindra Bank",
        "ticker": "KOTAKBANK.NS",
        "sector": "Banking",
        "headline": "FPI holding in Kotak Bank rises to 38.2% — 12-month high after RBI approval",
        "detail": "Foreign Portfolio Investors crossed 38% threshold after RBI enhanced ownership limit. Institutional confidence at all-time high, supported by clean asset quality metrics.",
        "value": "38.2% FPI holding",
        "signal_strength": 83,
        "date": _days_ago(3),
        "impact": "Strongly Bullish",
        "color": "#a78bfa",
        "icon": "globe",
        "historical_success_rate": 77,
        "avg_return_90d": 13.5,
    },
]

# FII/DII daily flow data
FII_DII_FLOW = [
    {"date": _days_ago(9), "fii_buy": 4210, "fii_sell": 5890, "fii_net": -1680, "dii_buy": 6120, "dii_sell": 4340, "dii_net": 1780},
    {"date": _days_ago(8), "fii_buy": 5340, "fii_sell": 4120, "fii_net": 1220,  "dii_buy": 4980, "dii_sell": 5210, "dii_net": -230},
    {"date": _days_ago(7), "fii_buy": 6780, "fii_sell": 5230, "fii_net": 1550,  "dii_buy": 5340, "dii_sell": 4890, "dii_net": 450},
    {"date": _days_ago(6), "fii_buy": 4560, "fii_sell": 6780, "fii_net": -2220, "dii_buy": 7120, "dii_sell": 4230, "dii_net": 2890},
    {"date": _days_ago(5), "fii_buy": 7890, "fii_sell": 5670, "fii_net": 2220,  "dii_buy": 5670, "dii_sell": 6120, "dii_net": -450},
    {"date": _days_ago(4), "fii_buy": 8230, "fii_sell": 5120, "fii_net": 3110,  "dii_buy": 4890, "dii_sell": 5340, "dii_net": -450},
    {"date": _days_ago(3), "fii_buy": 9120, "fii_sell": 6780, "fii_net": 2340,  "dii_buy": 5230, "dii_sell": 4780, "dii_net": 450},
    {"date": _days_ago(2), "fii_buy": 7650, "fii_sell": 5430, "fii_net": 2220,  "dii_buy": 6780, "dii_sell": 5120, "dii_net": 1660},
    {"date": _days_ago(1), "fii_buy": 8910, "fii_sell": 5670, "fii_net": 3240,  "dii_buy": 5430, "dii_sell": 4980, "dii_net": 450},
    {"date": _days_ago(0), "fii_buy": 6780, "fii_sell": 4320, "fii_net": 2460,  "dii_buy": 5890, "dii_sell": 4560, "dii_net": 1330},
]


@router.get("/radar", tags=["Opportunity Radar"])
async def get_radar_events(
    event_type: str = Query(None, description="Filter by event type"),
    impact: str = Query(None, description="Filter by impact: Bullish/Bearish/Cautionary"),
    limit: int = Query(10, le=50),
):
    """Return high-signal corporate events filtered by type or impact."""
    events = list(MOCK_RADAR_EVENTS)

    if event_type:
        events = [e for e in events if e["type"].lower() == event_type.lower()]
    if impact:
        events = [e for e in events if impact.lower() in e["impact"].lower()]

    events.sort(key=lambda e: e["signal_strength"], reverse=True)

    return {
        "events": events[:limit],
        "total": len(events),
        "event_types": list({e["type"] for e in MOCK_RADAR_EVENTS}),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/radar/fii-dii", tags=["Opportunity Radar"])
async def get_fii_dii_flow():
    """Return 10-day FII/DII activity flow data."""
    total_fii = sum(d["fii_net"] for d in FII_DII_FLOW)
    total_dii = sum(d["dii_net"] for d in FII_DII_FLOW)
    return {
        "flow": FII_DII_FLOW,
        "summary": {
            "fii_net_10d": total_fii,
            "dii_net_10d": total_dii,
            "fii_trend":   "Buying" if total_fii > 0 else "Selling",
            "dii_trend":   "Buying" if total_dii > 0 else "Selling",
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/radar/types", tags=["Opportunity Radar"])
async def get_event_types():
    """Return all radar event type counts."""
    from collections import Counter
    counts = Counter(e["type"] for e in MOCK_RADAR_EVENTS)
    return {"types": dict(counts)}
