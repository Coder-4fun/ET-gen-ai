"""
ET Markets Intelligence Layer — AI Explanation Agent

Generates retail-investor-friendly signal explanations using OpenRouter LLM.
Model: gpt-oss-20b via OpenRouter's OpenAI-compatible API.

System prompt follows SEBI analyst tone:
- Simple language, no jargon
- Never says 'buy' or 'sell' — uses 'worth watching' / 'caution advised'
- Under 80 words per explanation
- Falls back to rule-based templates if API is unavailable
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─── OpenRouter client (OpenAI-compatible) ────────────────────────────────────
def _get_openai_client():
    try:
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )
    except ImportError:
        return None

MODEL = os.getenv("OPENROUTER_MODEL", "gpt-oss-20b")

SYSTEM_PROMPT = """You are a SEBI-registered financial analyst explaining market signals 
to a first-time retail investor in India. Use simple, clear English language ONLY.  
CRITICAL: You MUST output all explanations in ENGLISH ONLY. Do NOT use Hindi, Devanagari script, Hinglish, or any other language.
Never say 'buy' or 'sell' — instead say 'worth watching' or 'caution advised'.  
Keep explanations under 80 words. Mention a specific price level if available."""

# ─── Rule-based fallback templates ───────────────────────────────────────────
FALLBACK_TEMPLATES = {
    "EarningsRisk": (
        "{stock} is seeing significant selling pressure. News sentiment turned negative after "
        "weaker-than-expected results. Social chatter is declining. "
        "Caution advised near ₹{price_level} support."
    ),
    "VolumeSpike": (
        "{stock} saw {volume_ratio:.1f}x normal trading volume today — likely driven by "
        "institutional activity ahead of a key event. Worth watching for a directional "
        "breakout above or below current levels."
    ),
    "BullishReversal": (
        "{stock} formed a {pattern} at key support. Volume confirmation makes this "
        "pattern stronger. Worth watching for follow-through above resistance. "
        "Backtest win rate: {win_rate:.0%}."
    ),
    "BearishReversal": (
        "{stock} showing {pattern} pattern near resistance. Selling pressure building. "
        "Caution advised if price stays below current levels. Watch ₹{price_level} as key support."
    ),
    "HighPCR": (
        "Institutional put buying on {stock} — PCR of {pcr:.2f} is elevated. "
        "Max pain near ₹{max_pain:,.0f} suggests price gravity near expiry. Caution advised."
    ),
    "UnusualCallOI": (
        "Heavy call buying on {stock} — PCR of {pcr:.2f} indicates bullish positioning. "
        "Institutions are betting on upside. Worth watching for follow-through."
    ),
    "SentimentSurge": (
        "{stock} trending on social media with {velocity:.1f}x normal buzz. "
        "Reddit and Twitter/X sentiment is strongly positive after recent news. "
        "Worth watching — momentum may continue."
    ),
    "SentimentCrash": (
        "{stock} social sentiment crashed — {velocity:.1f}x spike in negative mentions. "
        "Reddit and Twitter/X buzz turning bearish. Caution advised in the short term."
    ),
    "UpgradeDowngrade": (
        "{stock} received a fresh analyst action today. Positive re-rating suggests "
        "improving fundamentals. Worth watching for price discovery in the coming sessions."
    ),
    "MacroRisk": (
        "Broader macro signals affecting {stock} — RBI/Fed policy and FII flows "
        "creating uncertainty. Caution advised; watch broader NIFTY direction first."
    ),
    "FundamentalChange": (
        "{stock} undergoing a key fundamental shift. New product/partnership may "
        "re-rate the stock. Worth watching for volume confirmation."
    ),
}

DEFAULT_TEMPLATE = (
    "{stock} is showing a {signal} signal with {confidence:.0%} confidence. "
    "Worth monitoring closely. Backtest shows {win_rate:.0%} win rate over past signals."
)


def _build_llm_prompt(signal: dict) -> str:
    return f"""Stock: {signal.get('stock', 'UNKNOWN')}
Signal: {signal.get('signal', 'Unknown')}
Confidence: {signal.get('confidence', 0):.0%}
Sentiment Score: {signal.get('sentiment_score', 0):.2f}
Pattern Detected: {signal.get('pattern', 'None')}
Options PCR: {signal.get('pcr', 'N/A')}
Social Buzz: {signal.get('mention_velocity', 1):.1f}x normal
Backtest Win Rate: {signal.get('backtest_win_rate', 0):.0%}
Headline: {signal.get('headline', 'N/A')}

Explain this market signal for a retail investor in under 80 words.
CRITICAL: You MUST output all explanations in ENGLISH ONLY. Do NOT use Hindi or any other language."""


def _build_fallback_explanation(signal: dict) -> str:
    """Generate a rule-based explanation when LLM is unavailable."""
    signal_type = signal.get("signal", "")
    template = FALLBACK_TEMPLATES.get(signal_type, DEFAULT_TEMPLATE)

    try:
        return template.format(
            stock=signal.get("stock", "This stock"),
            signal=signal_type,
            confidence=signal.get("confidence", 0.7),
            pattern=signal.get("pattern", "pattern"),
            pcr=signal.get("pcr", 1.0),
            max_pain=signal.get("max_pain", 0),
            velocity=signal.get("mention_velocity", 1.0),
            volume_ratio=signal.get("volume_ratio", 1.0),
            win_rate=signal.get("backtest_win_rate", 0.6),
            price_level=signal.get("max_pain", 0),
        )
    except Exception:
        return DEFAULT_TEMPLATE.format(
            stock=signal.get("stock", "This stock"),
            signal=signal_type,
            confidence=signal.get("confidence", 0.7),
            win_rate=signal.get("backtest_win_rate", 0.6),
        )


async def generate_explanation(signal: dict) -> str:
    """
    Generate a human-readable explanation for a market signal.

    Tries OpenRouter LLM first; falls back to rule-based template.
    Returns explanation string.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "demo":
        logger.info("No OpenRouter API key — using rule-based explanation")
        return _build_fallback_explanation(signal)

    client = _get_openai_client()
    if client is None:
        return _build_fallback_explanation(signal)

    try:
        prompt = _build_llm_prompt(signal)
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7,
            extra_headers={
                "HTTP-Referer": "https://etmarkets.ai",
                "X-Title": "ET Markets Intelligence Layer",
            },
        )
        explanation = response.choices[0].message.content
        if explanation:
            explanation = explanation.strip()
            logger.info(f"✅ LLM explanation generated for {signal.get('stock')}")
            return explanation
        else:
            logger.warning(f"LLM returned empty content for {signal.get('stock')} — using fallback")
            return _build_fallback_explanation(signal)
    except Exception as e:
        logger.warning(f"LLM explanation failed ({e}) — using template fallback")
        return _build_fallback_explanation(signal)


async def enrich_signals_with_explanations(signals: list[dict]) -> list[dict]:
    """Generate explanations for a batch of signals."""
    import asyncio
    tasks = [generate_explanation(sig) for sig in signals]
    explanations = await asyncio.gather(*tasks, return_exceptions=True)
    for sig, exp in zip(signals, explanations):
        if isinstance(exp, str):
            sig["explanation"] = exp
        else:
            sig["explanation"] = _build_fallback_explanation(sig)
    return signals
