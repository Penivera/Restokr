import secrets
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token, verify_token_type
from app.core.redis import is_token_blacklisted
from app.core.logging import get_logger

logger = get_logger(__name__)

security = HTTPBasic()
bearer_security = HTTPBearer()


async def verify_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> HTTPBasicCredentials:
    """
    Verify admin credentials using HTTP Basic Auth.

    Args:
        credentials: HTTP Basic Auth credentials from request header

    Returns:
        Validated credentials

    Raises:
        HTTPException: If credentials are invalid
    """
    # Use constant-time comparison to prevent timing attacks
    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf-8"), settings.ADMIN_USERNAME.encode("utf-8")
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf-8"), settings.ADMIN_PASSWORD.encode("utf-8")
    )

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials


# Type alias for admin dependency
AdminDep = Annotated[HTTPBasicCredentials, Depends(verify_admin)]

# Type alias for database session dependency
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)],
    db: DBSessionDep,
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: Bearer token credentials from request header
        db: Database session

    Returns:
        Authenticated user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        logger.warning("Blacklisted token attempted access")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    if payload is None:
        logger.warning("Invalid JWT token received")
        raise credentials_exception

    # Verify token type
    if not verify_token_type(payload, "access"):
        raise credentials_exception

    # Extract user email from token
    email: Optional[str] = payload.get("sub")
    if email is None:
        logger.warning("JWT token missing subject claim")
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found for email: {email}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please activate your account first.",
        )

    logger.debug(f"Authenticated user: {email}")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current active user (already verified by get_current_user).

    Args:
        current_user: Current authenticated user

    Returns:
        Active user object
    """
    return current_user


# Type alias for current user dependency
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
