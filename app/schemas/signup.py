from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from app.models.signup import UserRole


class EarlyAccessSignupCreate(BaseModel):
    """Schema for creating early access signup."""
    
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of the user")
    email: EmailStr = Field(..., description="Valid email address")
    phone_number: PhoneNumber = Field(..., description="Phone number (will auto-prepend +234 if needed)")
    role: UserRole = Field(..., description="User role: customer, vendor, or rider")
    city: str = Field(default="Abuja", max_length=100, description="City location")
    
    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, v: str | PhoneNumber) -> str:
        """Auto-prepend +234 for Nigerian numbers if not provided."""
        if isinstance(v, PhoneNumber):
            return str(v)
        
        phone_str = str(v).strip()
        
        # Remove any spaces, dashes, or parentheses
        phone_str = phone_str.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # If already has country code, return as is
        if phone_str.startswith("+"):
            return phone_str
        
        # If starts with 234, add +
        if phone_str.startswith("234"):
            return f"+{phone_str}"
        
        # If starts with 0, replace with +234
        if phone_str.startswith("0"):
            return f"+234{phone_str[1:]}"
        
        # Otherwise, assume it's a local number and prepend +234
        return f"+234{phone_str}"
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "Adebayo Johnson",
                    "email": "adebayo@example.com",
                    "phone_number": "08012345678",
                    "role": "customer",
                    "city": "Abuja"
                }
            ]
        }
    }


class EarlyAccessSignupResponse(BaseModel):
    """Schema for early access signup response."""
    
    id: int
    full_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    city: str
    created_at: datetime
    email_confirmed: bool
    
    model_config = {"from_attributes": True}


class SignupListResponse(BaseModel):
    """Schema for paginated signup list."""
    
    total: int
    page: int
    page_size: int
    signups: list[EarlyAccessSignupResponse]


class ExportFormat(str):
    """Export format options."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
