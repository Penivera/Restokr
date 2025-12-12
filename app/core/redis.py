"""Redis client for token blacklisting and caching."""

from redis import asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis client instance
redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client

    try:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        # Ensure connection is alive; ping is async for aioredis client
        await redis_client.ping()
        logger.info(f"✅ Redis connected: {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("⚠️  Token blacklisting will not be available")
        redis_client = None


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client:
        try:
            await redis_client.aclose()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis: {e}")
        finally:
            redis_client = None


async def blacklist_token(token: str, expires_in: int) -> bool:
    """
    Add a token to the blacklist.

    Args:
        token: JWT token to blacklist
        expires_in: Token expiry time in seconds

    Returns:
        bool: True if successful, False otherwise
    """
    if not redis_client:
        logger.warning("Redis not available, token not blacklisted")
        return False

    try:
        key = f"blacklist:{token}"
        await redis_client.setex(key, expires_in, "1")
        logger.debug(f"Token blacklisted (expires in {expires_in}s)")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.

    Args:
        token: JWT token to check

    Returns:
        bool: True if blacklisted, False otherwise
    """
    if not redis_client:
        return False

    try:
        key = f"blacklist:{token}"
        result = await redis_client.exists(key)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        return False


def get_redis_client() -> Optional[Redis]:
    """Get the Redis client instance."""
    return redis_client
