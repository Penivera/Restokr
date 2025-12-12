"""Security utilities for password hashing and JWT token management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Custom expiration time delta (optional)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    logger.debug(
        f"Created access token for subject: {data.get('sub')} (expires: {expire})"
    )

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Custom expiration time delta (optional)

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    logger.debug(
        f"Created refresh token for subject: {data.get('sub')} (expires: {expire})"
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def generate_activation_token() -> str:
    """
    Generate a secure random activation token.

    Returns:
        str: Random hex token
    """
    return secrets.token_urlsafe(32)


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify the token type matches the expected type.

    Args:
        payload: Decoded JWT payload
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        bool: True if token type matches, False otherwise
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        logger.warning(
            f"Token type mismatch: expected {expected_type}, got {token_type}"
        )
        return False
    return True
