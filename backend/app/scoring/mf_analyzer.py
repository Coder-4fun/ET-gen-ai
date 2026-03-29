"""
ET Markets Intelligence Layer v2 — Mutual Fund Overlap Analyzer

Analyzes mutual fund portfolios for:
1. Stock overlap between funds (Jaccard similarity)
2. Concentration risk
3. Hidden sector exposure
4. Performance drag identification

Uses AMFI (MFAPI) for NAV data. Portfolio holdings are mock for hackathon.
"""

import logging
import random
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Mock MF portfolio data ──────────────────────────────────────────────────
# Realistic holdings for popular Indian mutual funds

MOCK_MF_PORTFOLIOS = {
    "119598": {
        "name": "Axis Bluechip Fund - Growth",
        "category": "Large Cap",
        "aum_cr": 34500,
        "nav": 52.34,
        "1y_return": 14.2,
        "holdings": {
            "HDFCBANK": 9.8, "ICICIBANK": 8.2, "RELIANCE": 7.5, "TCS": 6.8,
            "INFY": 6.1, "BAJFINANCE": 5.4, "BHARTIARTL": 4.8, "KOTAKBANK": 4.2,
            "LT": 3.9, "ITC": 3.6, "HINDUNILVR": 3.4, "AXISBANK": 3.1,
            "SBIN": 2.8, "SUNPHARMA": 2.5, "TITAN": 2.2,
        },
    },
    "120503": {
        "name": "Mirae Asset Large Cap Fund - Growth",
        "category": "Large Cap",
        "aum_cr": 38200,
        "nav": 95.67,
        "1y_return": 16.8,
        "holdings": {
            "HDFCBANK": 10.1, "RELIANCE": 8.9, "ICICIBANK": 7.3, "INFY": 6.5,
            "TCS": 5.8, "BHARTIARTL": 5.2, "BAJFINANCE": 4.6, "LT": 4.1,
            "SBIN": 3.8, "KOTAKBANK": 3.4, "NTPC": 3.1, "TATAMOTORS": 2.9,
            "SUNPHARMA": 2.6, "M&M": 2.3, "TITAN": 2.0,
        },
    },
    "118825": {
        "name": "SBI Focused Equity Fund - Growth",
        "category": "Focused",
        "aum_cr": 28900,
        "nav": 284.12,
        "1y_return": 18.5,
        "holdings": {
            "HDFCBANK": 8.5, "ICICIBANK": 7.8, "RELIANCE": 7.2, "TCS": 5.9,
            "BAJFINANCE": 5.5, "INFY": 5.1, "BHARTIARTL": 4.4, "LT": 4.0,
            "TATAMOTORS": 3.7, "WIPRO": 3.3, "SBIN": 3.0, "HAL": 2.8,
            "MARUTI": 2.5, "SUNPHARMA": 2.2, "KOTAKBANK": 2.0,
        },
    },
    "120716": {
        "name": "Parag Parikh Flexi Cap Fund - Growth",
        "category": "Flexi Cap",
        "aum_cr": 52100,
        "nav": 72.45,
        "1y_return": 21.2,
        "holdings": {
            "HDFCBANK": 6.2, "ICICIBANK": 5.8, "BAJFINANCE": 5.1, "ITC": 4.8,
            "COALINDIA": 4.5, "POWERGRID": 4.2, "RELIANCE": 3.9, "INFY": 3.6,
            "BHARTIARTL": 3.3, "NTPC": 3.0, "ONGC": 2.8, "SBIN": 2.5,
            "TRENT": 2.3, "M&M": 2.1, "TITAN": 1.8,
        },
    },
    "101209": {
        "name": "HDFC Mid-Cap Opportunities Fund - Growth",
        "category": "Mid Cap",
        "aum_cr": 41800,
        "nav": 168.90,
        "1y_return": 24.6,
        "holdings": {
            "ZOMATO": 4.2, "TRENT": 3.8, "MPHASIS": 3.5, "VOLTAS": 3.2,
            "CUMMINSIND": 3.0, "PIIND": 2.8, "HAVELLS": 2.6, "GODREJPROP": 2.4,
            "COLPAL": 2.2, "BHEL": 2.0, "TATAPOWER": 1.9, "ABB": 1.8,
            "DMART": 1.6, "DLF": 1.5, "AUROPHARMA": 1.4,
        },
    },
}


class MutualFundAnalyzer:
    """
    Analyzes mutual fund portfolio overlap, concentration, and sector exposure.
    """

    async def analyze_portfolio(self, scheme_codes: list[str]) -> dict:
        """Main entry: analyze overlap between selected mutual funds."""
        fund_portfolios = {}
        for code in scheme_codes:
            portfolio = await self._fetch_fund_portfolio(code)
            if portfolio:
                fund_portfolios[code] = portfolio

        if len(fund_portfolios) < 2:
            return {"error": "Need at least 2 valid funds for overlap analysis"}

        return {
            "funds": {
                code: {
                    "name": p["name"],
                    "category": p["category"],
                    "aum_cr": p["aum_cr"],
                    "nav": p["nav"],
                    "1y_return": p["1y_return"],
                    "stock_count": len(p["holdings"]),
                }
                for code, p in fund_portfolios.items()
            },
            "overlap_matrix": self._compute_overlap(fund_portfolios),
            "combined_holdings": self._merge_holdings(fund_portfolios),
            "concentration_risk": self._concentration_risk(fund_portfolios),
            "sector_exposure": self._sector_exposure(fund_portfolios),
            "recommendations": self._generate_recommendations(fund_portfolios),
            "timestamp": datetime.now().isoformat(),
        }

    async def _fetch_fund_portfolio(self, scheme_code: str) -> Optional[dict]:
        """Fetch fund portfolio. Uses mock data for hackathon."""
        if scheme_code in MOCK_MF_PORTFOLIOS:
            return MOCK_MF_PORTFOLIOS[scheme_code]

        # Try live MFAPI for NAV data
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"https://api.mfapi.in/mf/{scheme_code}")
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "name": data.get("meta", {}).get("scheme_name", f"Fund {scheme_code}"),
                        "category": data.get("meta", {}).get("scheme_category", "Unknown"),
                        "aum_cr": 0,
                        "nav": float(data["data"][0]["nav"]) if data.get("data") else 0,
                        "1y_return": 0,
                        "holdings": {},  # No public API for holdings
                    }
        except Exception as e:
            logger.warning(f"MFAPI fetch failed for {scheme_code}: {e}")

        return None

    def _compute_overlap(self, portfolios: dict) -> dict:
        """Compute pairwise overlap between funds using Jaccard similarity."""
        codes = list(portfolios.keys())
        matrix = {}

        for i, code_a in enumerate(codes):
            matrix[code_a] = {}
            stocks_a = set(portfolios[code_a]["holdings"].keys())
            name_a = portfolios[code_a]["name"]

            for code_b in codes:
                stocks_b = set(portfolios[code_b]["holdings"].keys())
                name_b = portfolios[code_b]["name"]
                intersection = stocks_a & stocks_b
                union = stocks_a | stocks_b
                jaccard = len(intersection) / len(union) if union else 0

                # Weighted overlap (by allocation %)
                weights_a = portfolios[code_a]["holdings"]
                weights_b = portfolios[code_b]["holdings"]
                weighted_overlap = sum(
                    min(weights_a.get(s, 0), weights_b.get(s, 0))
                    for s in intersection
                )

                matrix[code_a][code_b] = {
                    "fund_a": name_a,
                    "fund_b": name_b,
                    "jaccard": round(jaccard, 3),
                    "jaccard_pct": round(jaccard * 100, 1),
                    "common_stocks": sorted(intersection),
                    "common_count": len(intersection),
                    "weighted_overlap_pct": round(weighted_overlap, 1),
                    "risk_level": "High" if jaccard > 0.5 else ("Medium" if jaccard > 0.3 else "Low"),
                }

        return matrix

    def _merge_holdings(self, portfolios: dict) -> list[dict]:
        """Merge all holdings and compute effective combined allocation."""
        combined = defaultdict(lambda: {"weight_sum": 0, "funds": [], "max_weight": 0})
        total_funds = len(portfolios)

        for code, p in portfolios.items():
            for stock, weight in p["holdings"].items():
                combined[stock]["weight_sum"] += weight
                combined[stock]["funds"].append(p["name"])
                combined[stock]["max_weight"] = max(combined[stock]["max_weight"], weight)

        result = []
        for stock, data in combined.items():
            effective_weight = round(data["weight_sum"] / total_funds, 2)
            result.append({
                "stock": stock,
                "effective_weight": effective_weight,
                "fund_count": len(data["funds"]),
                "max_single_weight": data["max_weight"],
                "held_by": data["funds"],
                "concentration_flag": effective_weight > 6.0,
            })

        result.sort(key=lambda x: x["effective_weight"], reverse=True)
        return result[:20]

    def _concentration_risk(self, portfolios: dict) -> dict:
        """Assess concentration risk across combined portfolio."""
        merged = self._merge_holdings(portfolios)
        top5_weight = sum(h["effective_weight"] for h in merged[:5])
        top10_weight = sum(h["effective_weight"] for h in merged[:10])
        flagged = [h for h in merged if h["concentration_flag"]]

        return {
            "top5_concentration_pct": round(top5_weight, 1),
            "top10_concentration_pct": round(top10_weight, 1),
            "flagged_stocks": flagged,
            "risk_level": "High" if top5_weight > 35 else ("Medium" if top5_weight > 25 else "Low"),
            "message": (
                f"Top 5 stocks account for {top5_weight:.1f}% of your combined MF portfolio. "
                f"{'This is overly concentrated — consider diversifying.' if top5_weight > 35 else 'Concentration is within acceptable limits.'}"
            ),
        }

    def _sector_exposure(self, portfolios: dict) -> dict:
        """Compute effective sector exposure across all funds."""
        # Map stocks to sectors
        from app.ingestion.stock_universe import TIER_1_STOCKS, TIER_2_STOCKS
        stock_sector_map = {}
        for s in TIER_1_STOCKS + TIER_2_STOCKS:
            stock_sector_map[s["symbol"]] = s["sector"]

        sector_weights = defaultdict(float)
        total_weight = 0

        for code, p in portfolios.items():
            for stock, weight in p["holdings"].items():
                sector = stock_sector_map.get(stock, "Other")
                sector_weights[sector] += weight
                total_weight += weight

        sectors = []
        for sector, weight in sorted(sector_weights.items(), key=lambda x: -x[1]):
            pct = round(weight / total_weight * 100, 1) if total_weight else 0
            sectors.append({
                "sector": sector,
                "weight_pct": pct,
                "overweight": pct > 25,
            })

        return {"sectors": sectors}

    def _generate_recommendations(self, portfolios: dict) -> list[str]:
        """Generate actionable recommendations."""
        recs = []
        overlap = self._compute_overlap(portfolios)
        concentration = self._concentration_risk(portfolios)

        # Check for high overlap
        codes = list(portfolios.keys())
        for i, a in enumerate(codes):
            for b in codes[i + 1:]:
                j = overlap[a][b]["jaccard"]
                if j > 0.5:
                    recs.append(
                        f"⚠️ {overlap[a][b]['fund_a']} and {overlap[a][b]['fund_b']} have "
                        f"{overlap[a][b]['jaccard_pct']}% overlap. Consider replacing one."
                    )

        # Concentration
        if concentration["risk_level"] == "High":
            recs.append(
                f"⚠️ Top 5 stocks = {concentration['top5_concentration_pct']}% of portfolio. "
                "Add a mid-cap or sectoral fund for diversification."
            )

        if not recs:
            recs.append("✅ Your MF portfolio has healthy diversification. No immediate changes needed.")

        return recs

    def get_available_funds(self) -> list[dict]:
        """Return list of funds available for analysis."""
        return [
            {"scheme_code": code, "name": p["name"], "category": p["category"], "aum_cr": p["aum_cr"]}
            for code, p in MOCK_MF_PORTFOLIOS.items()
        ]


# ─── Module singleton ────────────────────────────────────────────────────────
_analyzer: Optional[MutualFundAnalyzer] = None


def get_mf_analyzer() -> MutualFundAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = MutualFundAnalyzer()
    return _analyzer
