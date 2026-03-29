"""
ET Markets Intelligence Layer — Social Media Ingestion

Fetches posts from Reddit (PRAW) and Twitter/X.
Falls back to mock social data in demo mode.
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

REDDIT_SUBREDDITS = ["IndianStockMarket", "Zerodha", "IndiaInvestments", "IndianStreetBets"]
TWITTER_KEYWORDS = ["NIFTY", "Sensex", "NSE", "$RELIANCE", "$ZOMATO", "$HDFCBANK", "Indian stocks"]

MOCK_POSTS = [
    {"platform": "reddit", "text": "Zomato Blinkit hits 1cr daily orders — massive milestone!", "score": 1240, "timestamp": datetime.now().isoformat(), "linked_stock": "ZOMATO"},
    {"platform": "reddit", "text": "HDFC Bank consolidating at 1580 — hammer pattern forming on daily. Looks bullish to me.", "score": 890, "timestamp": datetime.now().isoformat(), "linked_stock": "HDFCBANK"},
    {"platform": "reddit", "text": "Paytm RBI drama continues. I'm staying out till clarity on PA license.", "score": 672, "timestamp": datetime.now().isoformat(), "linked_stock": "PAYTM"},
    {"platform": "twitter", "text": "$TATAMOTORS EV launch! Nexon EV Pro 600km range. This is insane!", "score": 445, "timestamp": datetime.now().isoformat(), "linked_stock": "TATAMOTORS"},
    {"platform": "reddit", "text": "Reliance AGM coming up — usually a good catalyst. Watching 2900 breakout.", "score": 334, "timestamp": datetime.now().isoformat(), "linked_stock": "RELIANCE"},
    {"platform": "twitter", "text": "NIFTY breaking below 22100 support. FII selling pressure intense. Be careful!", "score": 567, "timestamp": datetime.now().isoformat(), "linked_stock": None},
    {"platform": "reddit", "text": "Zomato Q3 results terrible. Revenue miss of 12%. Exiting my position.", "score": 891, "timestamp": datetime.now().isoformat(), "linked_stock": "ZOMATO"},
    {"platform": "twitter", "text": "INFY upgrade by Morgan Stanley. Finally some positive news for IT sector!", "score": 231, "timestamp": datetime.now().isoformat(), "linked_stock": "INFY"},
]


def fetch_reddit_posts(stock: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Fetch Reddit posts for NSE stocks. Returns mock in demo mode."""
    mock_mode = os.getenv("MOCK_DATA", "true").lower() == "true"
    if mock_mode:
        posts = [p for p in MOCK_POSTS if p["platform"] == "reddit"]
        if stock:
            posts = [p for p in posts if p.get("linked_stock") == stock or p.get("linked_stock") is None]
        return posts[:limit]

    client_id = os.getenv("REDDIT_CLIENT_ID", "demo")
    if client_id == "demo":
        return [p for p in MOCK_POSTS if p["platform"] == "reddit"]

    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ETMarkets/1.0"),
        )
        posts = []
        for sub in REDDIT_SUBREDDITS:
            try:
                for submission in reddit.subreddit(sub).hot(limit=25):
                    posts.append({
                        "platform": "reddit",
                        "text": f"{submission.title} {submission.selftext[:200]}",
                        "score": submission.score,
                        "timestamp": datetime.fromtimestamp(submission.created_utc).isoformat(),
                        "url": submission.url,
                        "linked_stock": _extract_stock_mention(submission.title),
                    })
            except Exception as e:
                logger.warning(f"Reddit fetch failed for r/{sub}: {e}")
        return posts[:limit]
    except Exception as e:
        logger.warning(f"PRAW failed: {e}")
        return [p for p in MOCK_POSTS if p["platform"] == "reddit"]


def fetch_twitter_posts(stock: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Fetch Twitter/X posts. Returns mock in demo mode."""
    mock_mode = os.getenv("MOCK_DATA", "true").lower() == "true"
    if mock_mode:
        posts = [p for p in MOCK_POSTS if p["platform"] == "twitter"]
        if stock:
            posts = [p for p in posts if p.get("linked_stock") == stock or p.get("linked_stock") is None]
        return posts[:limit]

    bearer = os.getenv("TWITTER_BEARER_TOKEN", "demo")
    if bearer == "demo":
        return [p for p in MOCK_POSTS if p["platform"] == "twitter"]

    try:
        import httpx
        query = f"${stock} OR #{stock} lang:en -is:retweet" if stock else " OR ".join(TWITTER_KEYWORDS[:3]) + " lang:en -is:retweet"
        resp = httpx.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {bearer}"},
            params={"query": query, "max_results": min(limit, 100), "tweet.fields": "created_at,public_metrics"},
            timeout=10,
        )
        if resp.status_code == 200:
            tweets = resp.json().get("data", [])
            return [{
                "platform": "twitter",
                "text": t["text"],
                "score": t.get("public_metrics", {}).get("like_count", 0),
                "timestamp": t.get("created_at", datetime.now().isoformat()),
                "linked_stock": stock,
            } for t in tweets]
    except Exception as e:
        logger.warning(f"Twitter API failed: {e}")
    return [p for p in MOCK_POSTS if p["platform"] == "twitter"]


def _extract_stock_mention(text: str) -> Optional[str]:
    """Simple regex to extract stock mentions like $RELIANCE or ZOMATO from text."""
    import re
    known = ["RELIANCE", "ZOMATO", "HDFCBANK", "TATAMOTORS", "PAYTM", "INFY", "TCS", "WIPRO", "SBIN"]
    text_upper = text.upper()
    for stock in known:
        if stock in text_upper or f"${stock}" in text_upper:
            return stock
    return None
