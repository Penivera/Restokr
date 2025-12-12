from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        logger.warning("Quick fixes:")
        logger.warning("  1. Check PostgreSQL is running: brew services list")
        logger.warning("  2. Create database: createdb -U postgres restokr")
        logger.warning(
            "  3. Enable PostGIS: psql -U postgres -d restokr -c 'CREATE EXTENSION postgis;'"
        )
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
