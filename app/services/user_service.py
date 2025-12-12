import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks
from app.models.user import User
from app.schemas.user import UserCreate
from app.helpers.user_helpers import (
    hash_password,
    generate_activation,
    extract_conflicting_field,
)
from app.core.email import send_confirmation_email

logger = logging.getLogger(__name__)


async def create_user(
    data: UserCreate, db: AsyncSession, background_tasks: BackgroundTasks
) -> User:
    """
    Create a new local user.

    - Hashes password
    - Generates activation token
    - Inserts into DB
    - Handles unique constraint violations
    - Sends confirmation email
    """
    token, expiry = generate_activation()

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        phone_number=str(data.phone_number),
        role=data.role,
        city=data.city,
        password=hash_password(data.password),
        activation_token=token,
        activation_token_expiry=expiry,
    )

    try:
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)

        background_tasks.add_task(
            send_confirmation_email,
            to_email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
        )

        return new_user

    except IntegrityError as e:
        await db.rollback()
        # e.orig contains the original DBAPI exception
        error_msg = str(e.orig) if e.orig else str(e)
        conflict_field = extract_conflicting_field(error_msg)
        logger.warning(f"Unique constraint error on field: {conflict_field}")

        # Raise a structured exception your route layer will catch
        raise ValueError(f"{conflict_field} is already registered")

    except Exception:
        await db.rollback()
        logger.exception("Unexpected error during local user creation")
        raise
