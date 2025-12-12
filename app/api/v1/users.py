"""User endpoints for registration, authentication, and profile management."""

from datetime import datetime
from fastapi import APIRouter, status, BackgroundTasks, HTTPException
from sqlalchemy import select, update
from app.api.deps import DBSessionDep, CurrentActiveUserDep
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import (
    TokenResponse,
    UpdateUserRequest,
    MessageResponse,
    LoginRequest,
)
from app.services.user_service import create_user
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Local User Signup",
    description="Register a new local user account with password.",
)
async def register_user(
    signup_data: UserCreate,
    db: DBSessionDep,
    background_tasks: BackgroundTasks,
) -> User:
    """
    Register a new local user.

    - **full_name**: User's full name
    - **email**: Valid email address
    - **phone_number**: Phone number
    - **role**: User role
    - **city**: City location
    - **password**: Strong password
    """
    try:
        return await create_user(
            data=signup_data, db=db, background_tasks=background_tasks
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Local User Login",
)
async def login_user(
    login_data: LoginRequest,
    db: DBSessionDep,
) -> TokenResponse:
    """
    Authenticate local user with email and password.

    - **email**: User email address
    - **password**: User password
    """
    logger.info(f"Login attempt for email: {login_data.email}")

    # Fetch user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # Verify user exists and has a password (local account)
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


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: CurrentActiveUserDep,
) -> UserResponse:
    """Get current authenticated user's profile."""
    logger.info(f"Profile fetch for user: {current_user.email}")
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    current_user: CurrentActiveUserDep,
    db: DBSessionDep,
) -> UserResponse:
    """Update current authenticated user's profile."""
    logger.info(f"Profile update for user: {current_user.email}")

    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        return UserResponse.model_validate(current_user)

    await db.execute(
        update(User).where(User.id == current_user.id).values(**update_dict)
    )
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.delete("/me", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def deactivate_account(
    current_user: CurrentActiveUserDep,
    db: DBSessionDep,
) -> MessageResponse:
    """Deactivate current user's account."""
    logger.info(f"Account deactivation for user: {current_user.email}")

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(is_active=False, refresh_token=None)
    )
    await db.commit()

    return MessageResponse(
        message="Account deactivated successfully",
        detail="Your account has been deactivated. Contact support to reactivate.",
    )
