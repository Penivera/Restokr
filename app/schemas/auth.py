"""Authentication and user schemas."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole


# Request schemas
class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class SocialSignupRequest(BaseModel):
    """Social authentication signup/login request."""

    provider: Literal["google", "facebook", "apple"] = Field(
        ..., description="OAuth provider"
    )
    access_token: str = Field(..., description="Access token from OAuth provider")
    email: EmailStr = Field(..., description="User email from OAuth provider")
    full_name: str = Field(..., description="Full name from OAuth provider")
    provider_user_id: str = Field(..., description="Unique user ID from OAuth provider")
    role: UserRole = Field(..., description="User role: customer, vendor, or rider")
    city: str = Field(default="Abuja", description="User city")
    phone_number: Optional[str] = Field(None, description="Optional phone number")
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="Optional password for email/password login (enables hybrid auth)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password meets minimum strength requirements if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ActivateAccountRequest(BaseModel):
    """Account activation request schema."""

    email: EmailStr = Field(..., description="User email address")
    activation_token: str = Field(..., description="Activation token from email")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class UpdateUserRequest(BaseModel):
    """Update user profile request schema."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=r"^\+234\d{10}$")
    city: Optional[str] = Field(None, max_length=100)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Ensure phone number starts with +234."""
        if v is None:
            return v
        if not v.startswith("+234"):
            # Auto-prepend +234 if it's a 10-digit number
            if v.isdigit() and len(v) == 10:
                return f"+234{v}"
            raise ValueError(
                "Phone number must start with +234 or be a 10-digit number"
            )
        return v


# Response schemas
class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


class UserResponse(BaseModel):
    """User data response schema."""

    id: int
    email: EmailStr
    full_name: str
    phone_number: str
    role: UserRole
    city: str
    is_active: bool
    email_confirmed: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")
    detail: Optional[str] = Field(None, description="Additional details")
