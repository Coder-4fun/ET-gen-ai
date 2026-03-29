"""
ET Markets Intelligence Layer — Database Setup

Supports two modes:
1. SQLite (default, demo mode) — zero setup required
2. PostgreSQL (production) — set DATABASE_URL with asyncpg driver

Uses SQLAlchemy 2.0 async ORM throughout.
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./etmarkets.db")


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Create async engine — handle both SQLite and PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # SQLite needs check_same_thread=False
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Create all tables on startup (auto-migration for demo mode)."""
    from app import models  # noqa: F401 — imports models to register with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency: yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
