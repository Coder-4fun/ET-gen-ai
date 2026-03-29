"""
ET Markets Intelligence Layer — FinBERT NLP Signal Detector

Pipeline:
1. Preprocess and clean text (remove HTML, normalize entities)
2. Run FinBERT sentiment classification (positive/negative/neutral + score)
3. Extract named entities using spaCy NER (company names, numbers)
4. Classify signal type based on keyword rules + sentiment threshold
5. Return structured signal object

Falls back to VADER + keyword rules if FinBERT is unavailable.
"""

import os
import re
import uuid
import logging
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
logger = logging.getLogger(__name__)

# ─── FinBERT Lazy Loader ──────────────────────────────────────────────────────
_finbert_pipeline = None

def get_finbert_pipeline():
    """Lazily loads FinBERT — downloads model on first call (~500MB)."""
    global _finbert_pipeline
    if _finbert_pipeline is not None:
        return _finbert_pipeline

    use_finbert = os.getenv("USE_FINBERT", "true").lower() == "true"
    if not use_finbert:
        return None

    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        model_name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
        cache_dir = os.getenv("FINBERT_CACHE_DIR", "./models/finbert")

        logger.info(f"Loading FinBERT model: {model_name} …")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
        _finbert_pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            return_all_scores=True,
            device=-1,  # CPU inference
        )
        logger.info("✅ FinBERT loaded successfully")
        return _finbert_pipeline
    except Exception as e:
        logger.warning(f"⚠️  FinBERT failed to load ({e}) — falling back to VADER")
        return None


# ─── spaCy Lazy Loader ────────────────────────────────────────────────────────
_spacy_nlp = None

def get_spacy_nlp():
    """Lazily loads spaCy en_core_web_sm for NER."""
    global _spacy_nlp
    if _spacy_nlp is not None:
        return _spacy_nlp
    try:
        import spacy
        _spacy_nlp = spacy.load("en_core_web_sm")
        return _spacy_nlp
    except Exception as e:
        logger.warning(f"spaCy not available ({e})")
        return None


# ─── Signal Type Classification Rules ────────────────────────────────────────
SIGNAL_RULES = {
    "EarningsRisk": ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "quarterly", "results", "miss", "beat"],
    "InsiderActivity": ["insider", "promoter", "director", "bulk deal", "block deal", "stake", "acquisition"],
    "SentimentShift": ["downgrade", "upgrade", "analyst", "target", "recommendation", "outperform", "underperform"],
    "MacroRisk": ["rbi", "fed", "inflation", "rate", "gdp", "recession", "policy", "government", "budget", "sebi"],
    "UpgradeDowngrade": ["upgrade", "downgrade", "overweight", "underweight", "buy", "sell", "neutral", "price target"],
    "FundamentalChange": ["launch", "merger", "acquisition", "expansion", "new product", "partnership", "joint venture"],
}


def classify_signal_type(text: str, sentiment: str) -> str:
    """Classify signal type from text keywords and sentiment direction."""
    text_lower = text.lower()
    for signal_type, keywords in SIGNAL_RULES.items():
        if any(kw in text_lower for kw in keywords):
            return signal_type
    # Default based on sentiment
    return "SentimentShift" if sentiment in ("positive", "negative") else "MacroRisk"


def clean_text(text: str) -> str:
    """Remove HTML tags, URLs, and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:512]   # FinBERT max input length


def get_finbert_sentiment(text: str) -> tuple[str, float]:
    """
    Get sentiment label and score from FinBERT.
    Returns: (label: 'positive'|'negative'|'neutral', score: 0.0–1.0)
    """
    pipeline = get_finbert_pipeline()
    if pipeline is None:
        return _vader_fallback(text)

    try:
        raw_output = pipeline(text)[0]
        # Handle difference between transformers versions (list of dicts vs single dict)
        if isinstance(raw_output, list):
            best = max(raw_output, key=lambda x: x["score"])
        else:
            best = raw_output
            
        return best["label"].lower(), round(best["score"], 4)
    except Exception as e:
        logger.warning(f"FinBERT inference error: {e}")
        return _vader_fallback(text)


def _vader_fallback(text: str) -> tuple[str, float]:
    """VADER fallback sentiment (fast, no model needed)."""
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "positive", round(compound, 4)
    elif compound <= -0.05:
        return "negative", round(abs(compound), 4)
    else:
        return "neutral", round(1 - abs(compound), 4)


def extract_entities(text: str) -> list[str]:
    """Extract organization and financial entities using spaCy."""
    nlp = get_spacy_nlp()
    if nlp is None:
        return []
    try:
        doc = nlp(text[:512])
        return [ent.text for ent in doc.ents if ent.label_ in ("ORG", "MONEY", "PERCENT", "GPE")]
    except Exception:
        return []


# ─── Main Signal Detector ─────────────────────────────────────────────────────
def detect_signal_from_text(
    text: str,
    stock: str,
    ticker: str,
    source: str = "NewsAPI",
    headline: Optional[str] = None,
    sector: Optional[str] = None,
) -> dict:
    """
    Full NLP signal detection pipeline.

    Args:
        text: news article body or headline to analyze
        stock: stock symbol (e.g. 'ZOMATO')
        ticker: NSE ticker (e.g. 'ZOMATO.NS')
        source: data source name
        headline: optional shorter headline text
        sector: NIFTY sector

    Returns:
        Structured signal dict
    """
    clean = clean_text(headline or text)
    sentiment_label, sentiment_score = get_finbert_sentiment(clean)
    entities = extract_entities(clean)
    signal_type = classify_signal_type(clean, sentiment_label)

    # Confidence: driven by sentiment score + length of text
    confidence = round(min(0.95, sentiment_score * 1.1 + 0.05), 2)
    if sentiment_label == "neutral":
        confidence = round(confidence * 0.7, 2)

    # Risk level
    if confidence >= 0.80:
        risk = "High"
    elif confidence >= 0.60:
        risk = "Medium"
    else:
        risk = "Low"

    # Normalize sentiment score to -1 to +1 range
    norm_score = sentiment_score if sentiment_label == "positive" else -sentiment_score
    if sentiment_label == "neutral":
        norm_score = 0.0

    return {
        "id": f"sig_{uuid.uuid4().hex[:8]}",
        "stock": stock,
        "ticker": ticker,
        "sector": sector,
        "signal": signal_type,
        "confidence": confidence,
        "risk": risk,
        "strength": round(confidence * 5),
        "sentiment_score": round(norm_score, 3),
        "source": source,
        "headline": headline,
        "explanation": None,  # Filled by explanation_agent
        "contributing_signals": ["NLP"],
        "entities": entities,
        "timestamp": datetime.now().isoformat(),
    }


def batch_detect_signals(articles: list[dict]) -> list[dict]:
    """
    Detect signals from a batch of news articles.

    Each article dict should have: text, stock, ticker, source, headline (optional)
    """
    signals = []
    for article in articles:
        try:
            sig = detect_signal_from_text(
                text=article.get("body", article.get("headline", "")),
                stock=article.get("linked_stock", "UNKNOWN"),
                ticker=article.get("ticker", "UNKNOWN.NS"),
                source=article.get("source", "NewsAPI"),
                headline=article.get("headline"),
                sector=article.get("sector"),
            )
            signals.append(sig)
        except Exception as e:
            logger.error(f"Signal detection failed for article: {e}")
    return signals
