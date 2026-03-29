"""
ET Markets Intelligence Layer — AI Signal Chatbot Agent

Multi-turn conversational agent that answers questions about signals,
portfolio risk, and market conditions.

Context injected per query:
- Latest signals for portfolio stocks
- Current portfolio P&L summary
- Top sector performers
- Relevant past signals (semantic search via FAISS)

Streams responses via SSE (Server-Sent Events).
"""

import os
import json
import logging
from datetime import datetime
from typing import AsyncIterator, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = os.getenv("OPENROUTER_MODEL", "gpt-oss-20b")

SYSTEM_PROMPT = """You are ET Markets AI — a smart financial assistant for Indian retail investors.
You help users understand market signals, portfolio risk, candlestick patterns, and sector trends
focused on NSE/BSE stocks.

Rules:
- ALWAYS respond in English only. Never use Hindi, Devanagari script, or Hinglish.
- Never give direct buy/sell advice. Say 'worth watching' or 'caution advised'.
- Always reference specific signal data when available in context.
- Use simple language.
- Keep responses concise — under 150 words unless a detailed explanation is requested.
- Always mention confidence levels and backtest win rates when available.
- If asked about a stock not in context, say you'll need live data to answer accurately.
- Always cite sources in format [Source: NSE/BSE/SEBI/ET Markets Signal Engine]."""


def _get_openai_client():
    try:
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )
    except ImportError:
        return None


def _build_system_context(signals: list[dict], portfolio: dict) -> str:
    """Build context block injected into every chatbot message."""
    ctx = ["=== CURRENT MARKET CONTEXT ==="]

    if signals:
        ctx.append("\n📊 ACTIVE SIGNALS (Top 5 by confidence):")
        for s in signals[:5]:
            ctx.append(
                f"  • {s.get('stock')} | {s.get('signal')} | "
                f"{s.get('confidence', 0):.0%} conf | {s.get('risk', 'Medium')} risk"
                + (f" | Win rate: {s.get('backtest_win_rate', 0):.0%}" if s.get('backtest_win_rate') else "")
            )

    if portfolio and portfolio.get("holdings"):
        ctx.append("\n💼 PORTFOLIO SNAPSHOT:")
        summary = portfolio.get("summary", {})
        ctx.append(
            f"  Total P&L: ₹{summary.get('total_pnl', 0):,.0f} "
            f"({summary.get('total_pnl_percent', 0):+.2f}%)"
        )
        ctx.append(f"  Top gainer: {summary.get('top_gainer', 'N/A')} | "
                   f"Top loser: {summary.get('top_loser', 'N/A')}")
        for h in portfolio.get("holdings", [])[:3]:
            ctx.append(
                f"  • {h.get('stock')}: {h.get('qty')} shares | "
                f"P&L: ₹{h.get('unrealized_pnl', 0):,.0f} ({h.get('pnl_percent', 0):+.1f}%)"
            )

    ctx.append(f"\n⏰ Data as of: {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}")
    return "\n".join(ctx)


def _fallback_response(message: str, signals: list[dict], portfolio: dict) -> str:
    """Rule-based chatbot response when LLM is unavailable."""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["top signal", "best signal", "highest confidence"]):
        if signals:
            top = max(signals, key=lambda s: s.get("confidence", 0))
            return (
                f"🎯 Top signal right now: **{top.get('stock')}** — {top.get('signal')} "
                f"with {top.get('confidence', 0):.0%} confidence ({top.get('risk')} risk). "
                f"{top.get('explanation', '')}"
            )

    if any(w in msg_lower for w in ["portfolio", "p&l", "holding", "loss", "gain"]):
        summary = portfolio.get("summary", {})
        pnl = summary.get("total_pnl", 0)
        pct = summary.get("total_pnl_percent", 0)
        emoji = "📈" if pnl >= 0 else "📉"
        return (
            f"{emoji} Your portfolio is currently showing ₹{abs(pnl):,.0f} "
            f"{'profit' if pnl >= 0 else 'loss'} ({pct:+.2f}%). "
            f"Top gainer: {summary.get('top_gainer', 'N/A')}, "
            f"Top loser: {summary.get('top_loser', 'N/A')}. "
            f"You have {summary.get('active_signals_count', 0)} active signals on your holdings."
        )

    if any(w in msg_lower for w in ["zomato", "reliance", "hdfc", "paytm", "tata"]):
        stock_name = next(
            (w.upper() for w in ["ZOMATO", "RELIANCE", "HDFCBANK", "PAYTM", "TATAMOTORS"]
             if w.lower() in msg_lower), None)
        if stock_name:
            sig = next((s for s in signals if s.get("stock") == stock_name), None)
            if sig:
                return (
                    f"📊 **{stock_name}** signal: {sig.get('signal')} | "
                    f"Confidence: {sig.get('confidence', 0):.0%} | Risk: {sig.get('risk')}. "
                    f"{sig.get('explanation', 'No explanation available.')}"
                )

    return (
        "I'm ET Markets AI 🤖. I can help you with:\n"
        "• **Top signals today** — ask 'What are the top signals?'\n"
        "• **Portfolio analysis** — ask 'How is my portfolio doing?'\n"
        "• **Stock-specific signals** — ask 'Why is ZOMATO flashing a signal?'\n"
        "• **Sector analysis** — ask 'Which sector is performing best?'\n\n"
        "What would you like to know?"
    )


async def stream_chat_response(
    message: str,
    session_history: list[dict],
    signals: list[dict],
    portfolio: dict,
) -> AsyncIterator[str]:
    """
    Stream chat response via SSE.
    Priority: Claude → OpenRouter → Rule-based fallback.
    Yields text chunks as they arrive from the LLM.
    """
    # ── Try Claude first (best quality, portfolio-aware) ──────────────
    try:
        from app.intelligence.claude_client import get_claude_client
        claude = get_claude_client()
        if claude:
            # Build Claude-compatible messages (last 6 turns + new message)
            claude_messages = []
            for turn in session_history[-6:]:
                claude_messages.append({"role": turn["role"], "content": turn["content"]})
            claude_messages.append({"role": "user", "content": message})

            # Build portfolio context for Claude
            portfolio_context = None
            if portfolio and portfolio.get("holdings"):
                portfolio_context = {
                    "holdings": {h["stock"]: h for h in portfolio.get("holdings", [])},
                    "summary": portfolio.get("summary", {}),
                }

            # Build market context from signals
            market_context = {
                "active_signals": len(signals),
                "top_signals": [
                    {"stock": s.get("stock"), "signal": s.get("signal") or s.get("signal_type"),
                     "confidence": s.get("confidence", 0), "risk": s.get("risk", "Medium")}
                    for s in sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True)[:5]
                ],
            }

            async for chunk in claude.stream_chat(claude_messages, portfolio_context, market_context):
                yield chunk
            return
    except Exception as e:
        logger.info(f"Claude chat unavailable ({e}), trying OpenRouter...")

    # ── Try OpenRouter ────────────────────────────────────────────────
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if api_key and api_key != "demo":
        client = _get_openai_client()
        if client:
            context_block = _build_system_context(signals, portfolio)
            system_with_context = f"{SYSTEM_PROMPT}\n\n{context_block}"

            messages = [{"role": "system", "content": system_with_context}]
            for turn in session_history[-6:]:
                messages.append({"role": turn["role"], "content": turn["content"]})
            messages.append({"role": "user", "content": message})

            try:
                stream = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.8,
                    stream=True,
                    extra_headers={
                        "HTTP-Referer": "https://etmarkets.ai",
                        "X-Title": "ET Markets Intelligence Layer",
                    },
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return
            except Exception as e:
                logger.warning(f"OpenRouter streaming failed ({e})")

    # ── Rule-based fallback ───────────────────────────────────────────
    yield _fallback_response(message, signals, portfolio)


async def get_chat_response(
    message: str,
    session_history: list[dict],
    signals: list[dict],
    portfolio: dict,
) -> str:
    """Non-streaming version — returns full response string."""
    chunks = []
    async for chunk in stream_chat_response(message, session_history, signals, portfolio):
        chunks.append(chunk)
    return "".join(chunks)
