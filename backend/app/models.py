"""
ET Markets Intelligence Layer — SQLAlchemy ORM Models

Models:
- Signal: a detected market signal with metadata
- PortfolioHolding: user's stock holding with P&L fields
- Alert: sent alert log
- ChatMessage: chatbot conversation history
- BacktestResult: persisted backtest output
- NewsArticle: processed news with sentiment
"""

from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    stock: Mapped[str] = mapped_column(String(20), index=True)
    ticker: Mapped[str] = mapped_column(String(30))
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    signal: Mapped[str] = mapped_column(String(50))         # e.g. EarningsRisk
    confidence: Mapped[float] = mapped_column(Float)
    risk: Mapped[str] = mapped_column(String(20))           # High/Medium/Low
    strength: Mapped[int] = mapped_column(Integer)          # 1–5
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50))
    headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pcr: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_pain: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    mention_velocity: Mapped[float | None] = mapped_column(Float, nullable=True)
    contributing_signals: Mapped[list | None] = mapped_column(JSON, nullable=True)
    backtest_win_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    backtest_avg_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    stock: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ticker: Mapped[str] = mapped_column(String(30))
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qty: Mapped[int] = mapped_column(Integer)
    avg_buy_price: Mapped[float] = mapped_column(Float)
    buy_date: Mapped[str] = mapped_column(String(20))
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock: Mapped[str] = mapped_column(String(20))
    signal_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float)
    channel: Mapped[str] = mapped_column(String(20))        # email / whatsapp / in-app
    message: Mapped[str] = mapped_column(Text)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))           # user / assistant
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(50))
    win_rate: Mapped[float] = mapped_column(Float)
    avg_return: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    total_signals: Mapped[int] = mapped_column(Integer)
    backtest_period: Mapped[str] = mapped_column(String(100))
    equity_curve: Mapped[list | None] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    headline: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime)
    linked_stock: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
