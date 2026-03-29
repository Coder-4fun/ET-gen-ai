"""
ET Markets Intelligence Layer v2 — Claude Client

Direct Anthropic Claude client for all AI generation.
Replaces OpenRouter for lower latency, higher reliability, and better prompting control.

Falls back to OpenRouter if ANTHROPIC_API_KEY is not set.
"""

import os
import json
import logging
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)

# Check which AI provider to use
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
USE_CLAUDE = bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "demo")

SEBI_ANALYST_SYSTEM = """You are a SEBI-registered research analyst with 15 years of 
experience on Dalal Street. You write clear, accurate, actionable signal explanations 
for Indian retail investors.

LANGUAGE: Always respond in English only. Never use Hindi, Devanagari script, or Hinglish.

TONE RULES:
- Never say "I think" or "possibly" — be direct and factual
- Use Indian number system (lakh/crore, never million/billion)
- Reference Indian market context (NSE, BSE, SEBI regulations)
- Avoid jargon — explain technical terms inline
- End with one specific, actionable implication

OUTPUT: Always return valid JSON only. No markdown. No preamble."""


class ClaudeClient:
    """Direct Anthropic Claude client for all AI generation."""

    def __init__(self):
        self.client = None
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self._initialized = False

    def _ensure_client(self):
        """Lazy-init the Anthropic client."""
        if not self._initialized:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
                self._initialized = True
                logger.info(f"🤖 Claude client initialized (model: {self.model})")
            except ImportError:
                logger.warning("anthropic package not installed — pip install anthropic")
                self.client = None
            except Exception as e:
                logger.warning(f"Claude init failed: {e}")
                self.client = None

    async def explain_signal(self, signal: dict, portfolio_context: dict = None) -> Optional[dict]:
        """Generate investor-friendly signal explanation via Claude."""
        self._ensure_client()
        if not self.client:
            return None

        portfolio_note = ""
        if portfolio_context and signal.get("stock") in portfolio_context.get("holdings", {}):
            holding = portfolio_context["holdings"][signal["stock"]]
            portfolio_note = f"""
USER PORTFOLIO CONTEXT:
- User holds {holding.get('qty', 0)} shares at avg ₹{holding.get('avg_price', 0):,.0f}
- Current value: ₹{holding.get('current_value', 0):,.0f}
- Current PnL: {'+' if holding.get('pnl', 0) > 0 else ''}₹{holding.get('pnl', 0):,.0f}
Personalize the explanation around how this signal affects their existing position."""

        prompt = f"""Analyze this market signal and return a JSON explanation:

SIGNAL DATA:
{json.dumps(signal, indent=2, default=str)}
{portfolio_note}

Return ONLY this JSON structure:
{{
  "headline": "<10-15 word punchy headline>",
  "summary": "<2-3 sentence plain English explanation, factual, no hedging>",
  "why_it_matters": "<1-2 sentences on market mechanism — why does this signal matter?>",
  "portfolio_impact": "<personalized impact if portfolio context provided, else null>",
  "key_level_to_watch": "<specific price level (support/resistance/target) if applicable>",
  "risk_factor": "<1 sentence on what would invalidate this signal>",
  "time_horizon": "intraday|swing|positional|investment",
  "action_suggestion": "buy_on_dip|add|hold|reduce|avoid|watch",
  "confidence_reasoning": "<2-3 sentence chain-of-thought on why confidence is {signal.get('confidence', 0.5):.0%}>"
}}"""

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=SEBI_ANALYST_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Claude returned non-JSON for signal explanation")
            return None
        except Exception as e:
            logger.warning(f"Claude explain_signal failed: {e}")
            return None

    async def stream_chat(
        self,
        messages: list,
        portfolio_context: dict = None,
        market_context: dict = None,
    ) -> AsyncIterator[str]:
        """Streaming chat for AI Market Assistant."""
        self._ensure_client()
        if not self.client:
            yield "Claude AI is not configured. Please set ANTHROPIC_API_KEY."
            return

        system = f"""{SEBI_ANALYST_SYSTEM}

REAL-TIME MARKET CONTEXT (as of now):
{json.dumps(market_context or {}, indent=2, default=str)}

USER PORTFOLIO:
{json.dumps(portfolio_context or {}, indent=2, default=str)}

For portfolio-related questions, always reference the user's specific holdings.
Always cite your data sources in the format [Source: NSE/BSE/SEBI/ET Markets].
If a question requires real-time data you don't have, say so clearly."""

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Claude chat stream error: {e}")
            yield f"AI response error: {str(e)}"

    async def generate_regime_analysis(self, market_data: dict) -> Optional[dict]:
        """Detect current market regime for signal calibration."""
        self._ensure_client()
        if not self.client:
            return None

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=SEBI_ANALYST_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze current market regime from this data:
{json.dumps(market_data, indent=2, default=str)}

Return JSON:
{{
  "regime": "strong_bull|weak_bull|sideways|weak_bear|strong_bear",
  "confidence": <0-100>,
  "key_indicator": "<what's driving the regime>",
  "signal_multiplier": <0.7-1.3>,
  "reasoning": "<2 sentences>"
}}"""
                }],
            )
            return json.loads(message.content[0].text.strip())
        except Exception as e:
            logger.warning(f"Claude regime analysis failed: {e}")
            return None


# ─── Module singleton ────────────────────────────────────────────────────────
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> Optional[ClaudeClient]:
    """Get Claude client singleton. Returns None if not configured."""
    global _claude_client
    if not USE_CLAUDE:
        return None
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
