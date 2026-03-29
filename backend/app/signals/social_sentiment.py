"""
ET Markets Intelligence Layer — Social Sentiment Fusion

Aggregates Reddit + Twitter/X sentiment using VADER + FinBERT weighted scoring.

Steps:
1. Collect posts from social_ingestion module
2. Score each post with VADER (fast) + FinBERT (deep) at 40/60 weight
3. Compute aggregate metrics: sentiment_score, velocity, consensus
4. Trigger: SentimentSurge, SentimentCrash, ViralMention
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)
vader = SentimentIntensityAnalyzer()


def score_post_vader(text: str) -> float:
    """Returns VADER compound score -1 to +1."""
    scores = vader.polarity_scores(text)
    return scores["compound"]


def score_post_finbert(text: str) -> float:
    """Returns FinBERT score -1 to +1 (lazy load)."""
    try:
        from app.signals.signal_detector import get_finbert_pipeline
        pipeline = get_finbert_pipeline()
        if pipeline is None:
            return score_post_vader(text)

        result = pipeline(text[:512])[0]
        best = max(result, key=lambda x: x["score"])
        label = best["label"].lower()
        score = best["score"]
        if label == "positive":
            return score
        elif label == "negative":
            return -score
        else:
            return 0.0
    except Exception:
        return score_post_vader(text)


def score_post(text: str, use_finbert_weight: float = 0.6) -> float:
    """
    Weighted sentiment score: VADER (40%) + FinBERT (60%).
    Returns value in range [-1, +1].
    """
    vader_score = score_post_vader(text)
    finbert_score = score_post_finbert(text)
    return round(
        vader_score * (1 - use_finbert_weight) + finbert_score * use_finbert_weight,
        4
    )


def compute_mention_velocity(posts: list[dict]) -> float:
    """
    Compute how fast mentions are growing.
    Compares recent 6h mentions vs prior 18h (normalized to same window).
    Returns velocity ratio (>3 = SentimentSurge trigger).
    """
    from datetime import timedelta
    now = datetime.now()

    recent_count = 0
    older_count = 0

    for post in posts:
        try:
            ts_str = post.get("timestamp", "")
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else now
            ts = ts.replace(tzinfo=None)
            age_hours = (now - ts).total_seconds() / 3600
            if age_hours <= 6:
                recent_count += 1
            elif age_hours <= 24:
                older_count += 1
        except Exception:
            recent_count += 1

    if older_count == 0:
        return round(min(5.0, recent_count * 0.5), 2)

    # Normalize older bucket to 6h equivalent
    older_6h_equiv = older_count / 3
    if older_6h_equiv == 0:
        return 5.0
    return round(min(10.0, recent_count / older_6h_equiv), 2)


def fuse_social_sentiment(
    posts_reddit: list[dict],
    posts_twitter: list[dict],
    stock: str,
    ticker: str,
    sector: Optional[str] = None,
) -> Optional[dict]:
    """
    Fuse Reddit + Twitter sentiment into a unified signal.

    Each post dict should have: text, timestamp, score (upvotes/likes), platform

    Returns:
        Signal dict or None if insufficient data.
    """
    all_posts = posts_reddit + posts_twitter
    if not all_posts:
        return None

    # ── Score each post ─────────────────────────────────────────────────────
    scored_posts = []
    for post in all_posts:
        text = post.get("text", post.get("title", ""))
        if not text:
            continue
        s = score_post(text)
        engagement = max(1, post.get("score", post.get("likes", 1)))
        scored_posts.append({"score": s, "engagement": engagement, "platform": post.get("platform", "reddit")})

    if not scored_posts:
        return None

    # ── Weighted average by engagement ─────────────────────────────────────
    total_weight = sum(p["engagement"] for p in scored_posts)
    weighted_score = sum(p["score"] * p["engagement"] for p in scored_posts) / total_weight

    # ── Platform breakdown ────────────────────────────────────────────────
    reddit_posts = [p for p in scored_posts if p["platform"] == "reddit"]
    twitter_posts = [p for p in scored_posts if p["platform"] in ("twitter", "x")]

    reddit_avg = round(sum(p["score"] for p in reddit_posts) / len(reddit_posts), 3) if reddit_posts else None
    twitter_avg = round(sum(p["score"] for p in twitter_posts) / len(twitter_posts), 3) if twitter_posts else None

    # ── Mention velocity ──────────────────────────────────────────────────
    velocity = compute_mention_velocity(all_posts)

    # ── Consensus stats ───────────────────────────────────────────────────
    bullish_count = sum(1 for p in scored_posts if p["score"] > 0.1)
    bearish_count = sum(1 for p in scored_posts if p["score"] < -0.1)
    consensus_pct_bullish = round(bullish_count / len(scored_posts) * 100, 1)

    # ── Signal classification ─────────────────────────────────────────────
    total_mentions = len(all_posts)
    if velocity >= 3.0 and weighted_score > 0.4:
        signal_type = "SentimentSurge"
        confidence = round(min(0.92, 0.55 + weighted_score * 0.3 + (velocity - 3) * 0.02), 2)
        risk = "Low"
    elif velocity >= 3.0 and weighted_score < -0.4:
        signal_type = "SentimentCrash"
        confidence = round(min(0.92, 0.55 + abs(weighted_score) * 0.3 + (velocity - 3) * 0.02), 2)
        risk = "High"
    elif total_mentions >= 50 and velocity >= 2.0:
        signal_type = "ViralMention"
        confidence = round(min(0.78, 0.55 + velocity * 0.02), 2)
        risk = "Medium"
    else:
        return None  # Not enough signal

    # ── Top post ──────────────────────────────────────────────────────────
    top = max(all_posts, key=lambda p: p.get("score", p.get("likes", 0)))
    top_text = top.get("text", top.get("title", ""))[:200]

    return {
        "id": f"sig_{uuid.uuid4().hex[:8]}",
        "stock": stock,
        "ticker": ticker,
        "sector": sector,
        "signal": signal_type,
        "confidence": confidence,
        "risk": risk,
        "strength": round(confidence * 5),
        "sentiment_score": round(float(weighted_score), 3),
        "mention_velocity": velocity,
        "total_mentions": total_mentions,
        "consensus_pct_bullish": consensus_pct_bullish,
        "top_reddit_post": top_text if top.get("platform") == "reddit" else None,
        "top_twitter_post": top_text if top.get("platform") in ("twitter", "x") else None,
        "platform_breakdown": {
            "reddit": reddit_avg,
            "twitter": twitter_avg,
        },
        "source": "SocialSentiment",
        "contributing_signals": ["SocialSentiment"],
        "timestamp": datetime.now().isoformat(),
    }
