from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography
from app.database import Base


class UserRole(str, Enum):
    """User role enumeration."""

    CUSTOMER = "customer"
    VENDOR = "vendor"
    RIDER = "rider"


class User(Base):
    """User model with geolocation support."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, index=True
    )

    # Authentication fields
    password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Hashed password for user accounts"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Account activated status"
    )

    # Social authentication
    auth_provider: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="OAuth provider: google, facebook, apple"
    )
    provider_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Unique ID from OAuth provider"
    )
    activation_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Token for account activation"
    )
    activation_token_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Activation token expiry time"
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Current refresh token"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last successful login time"
    )

    # Location information
    city: Mapped[str] = mapped_column(String(100), default="Abuja", nullable=False)
    location: Mapped[Optional[str]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment="GPS coordinates for future mapping features",
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    is_exported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email} - {self.role.value}>"
