"""Authentication endpoints for login, logout, refresh tokens, and account activation."""

from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select, update, or_
from app.api.deps import DBSessionDep, CurrentUserDep
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    ActivateAccountRequest,
    MessageResponse,
    SocialSignupRequest,
    LoginRequest,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    generate_activation_token,
)
from app.core.redis import blacklist_token
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: DBSessionDep,
) -> TokenResponse:
    """
    Authenticate user with email and password.

    Args:
        login_data: Login credentials (email and password)
        db: Database session

    Returns:
        JWT tokens for authentication

    Raises:
        HTTPException: If credentials are invalid or account not activated
    """
    logger.info(f"Login attempt for email: {login_data.email}")

    # Fetch user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if (
        not user
        or not user.password
        or not verify_password(login_data.password, user.password)
    ):
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is activated
    if not user.is_active:
        logger.warning(f"Inactive account login attempt: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please check your email for activation instructions.",
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Update user's refresh token and last login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(refresh_token=refresh_token, last_login=datetime.utcnow())
    )
    await db.commit()

    logger.info(f"Successful login for user: {login_data.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    authorization: str = Header(...),
) -> MessageResponse:
    """
    Logout user by blacklisting their access token.

    Args:
        current_user: Currently authenticated user
        db: Database session
        authorization: Authorization header with Bearer token

    Returns:
        Success message
    """
    logger.info(f"Logout request for user: {current_user.email}")

    # Extract token from Authorization header
    token = authorization.replace("Bearer ", "").strip()

    # Blacklist the access token
    token_expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await blacklist_token(token, token_expires_in)

    # Clear refresh token in database
    await db.execute(
        update(User).where(User.id == current_user.id).values(refresh_token=None)
    )
    await db.commit()

    logger.info(f"User logged out successfully: {current_user.email}")

    return MessageResponse(
        message="Successfully logged out",
        detail="Your access token has been blacklisted",
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: DBSessionDep,
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    logger.info("Access token refresh attempt")

    # Decode refresh token
    payload = decode_token(request.refresh_token)
    if payload is None or not verify_token_type(payload, "refresh"):
        logger.warning("Invalid refresh token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract email from token
    email = payload.get("sub")
    if not email:
        logger.warning("Refresh token missing subject claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Verify user exists and token matches stored token
    if not user or user.refresh_token != request.refresh_token:
        logger.warning(f"Refresh token mismatch for user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is still active
    if not user.is_active:
        logger.warning(f"Inactive account refresh attempt: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    # Update refresh token in database
    await db.execute(
        update(User).where(User.id == user.id).values(refresh_token=new_refresh_token)
    )
    await db.commit()

    logger.info(f"Access token refreshed for user: {email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/activate", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def activate_account(
    request: ActivateAccountRequest,
    db: DBSessionDep,
) -> MessageResponse:
    """
    Activate user account with activation token and set password.

    Args:
        request: Activation request with email, token, and password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If activation token is invalid or expired
    """
    logger.info(f"Account activation attempt for email: {request.email}")

    # Fetch user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Activation attempt for non-existent user: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already activated
    if user.is_active:
        logger.info(f"Activation attempt for already active account: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already activated",
        )

    # Verify activation token
    if user.activation_token != request.activation_token:
        logger.warning(f"Invalid activation token for user: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token",
        )

    # Check token expiry
    if (
        user.activation_token_expiry
        and user.activation_token_expiry < datetime.utcnow()
    ):
        logger.warning(f"Expired activation token for user: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired. Please request a new one.",
        )

    # Activate account
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            is_active=True,
            activation_token=None,
            activation_token_expiry=None,
        )
    )
    await db.commit()

    logger.info(f"Account activated successfully for user: {request.email}")

    return MessageResponse(
        message="Account activated successfully",
        detail="You can now log in with your email and password",
    )


@router.post(
    "/resend-activation", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def resend_activation_token(
    email: str,
    db: DBSessionDep,
) -> MessageResponse:
    """
    Resend activation token to user's email.

    Args:
        email: User email address
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or already activated
    """
    logger.info(f"Activation token resend request for email: {email}")

    # Fetch user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Resend activation attempt for non-existent user: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_active:
        logger.info(f"Resend activation attempt for already active account: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already activated",
        )

    # Generate new activation token
    new_token = generate_activation_token()
    expiry = datetime.utcnow() + timedelta(days=7)

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(activation_token=new_token, activation_token_expiry=expiry)
    )
    await db.commit()

    # TODO: Send activation email with new token
    # This would be implemented in the email service

    logger.info(f"New activation token generated for user: {email}")

    return MessageResponse(
        message="Activation email sent",
        detail="Please check your email for the new activation link",
    )


@router.post(
    "/social/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def social_signup(
    request: SocialSignupRequest,
    db: DBSessionDep,
) -> TokenResponse:
    """
    Sign up or log in via social OAuth provider (Google, Facebook, Apple).

    Frontend handles OAuth flow and passes the provider access token.
    Backend verifies and creates/authenticates the user.

    Args:
        request: Social signup request with provider details
        db: Database session

    Returns:
        JWT tokens for authentication
    """
    logger.info(f"Social {request.provider} signup/login for email: {request.email}")

    # Check if user already exists (by email or provider_user_id)
    result = await db.execute(
        select(User).where(
            or_(
                User.email == request.email,
                User.provider_user_id == request.provider_user_id,
            )
        )
    )
    user = result.scalar_one_or_none()

    if user:
        # User exists - log them in
        logger.info(f"Existing user social login: {request.email}")

        # Update provider info and password if provided
        update_values = {}
        if not user.auth_provider:
            update_values["auth_provider"] = request.provider
            update_values["provider_user_id"] = request.provider_user_id
            update_values["is_active"] = True

        # Set password if provided (enables hybrid auth)
        if request.password:
            hashed_password = get_password_hash(request.password)
            update_values["password"] = hashed_password
            logger.info(f"Password set for social user: {request.email}")

        if update_values:
            await db.execute(
                update(User).where(User.id == user.id).values(**update_values)
            )
            await db.commit()
            await db.refresh(user)
    else:
        # Create new user
        logger.info(f"Creating new user via {request.provider}: {request.email}")

        # Hash password if provided
        hashed_password = None
        if request.password:
            hashed_password = get_password_hash(request.password)
            logger.info(f"Password set during social signup: {request.email}")

        user = User(
            full_name=request.full_name,
            email=request.email,
            phone_number=request.phone_number
            or f"+234{datetime.utcnow().timestamp():.0f}",  # Placeholder
            role=request.role,
            city=request.city,
            auth_provider=request.provider,
            provider_user_id=request.provider_user_id,
            password=hashed_password,  # Optional password for hybrid auth
            is_active=True,  # Social users are auto-activated
            email_confirmed=True,  # Email verified by OAuth provider
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user created via social login: {request.email}")

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Update user's refresh token and last login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(refresh_token=refresh_token, last_login=datetime.utcnow())
    )
    await db.commit()

    logger.info(f"Social authentication successful for user: {request.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
