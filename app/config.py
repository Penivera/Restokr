from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = Field(default="ReStockr API")
    VERSION: str = Field(default="1.0.0")
    API_PREFIX: str = Field(default="v1", description="API version prefix")
    DESCRIPTION: str = Field(
        default="Hyper-local restocking platform connecting customers, vendors, and riders"
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:admin@localhost/restokr",
        description="Async PostgreSQL connection string",
    )
    DATABASE_ECHO: bool = Field(default=False, description="Log SQL queries")

    # Admin Authentication
    ADMIN_USERNAME: str = Field(default="admin")
    ADMIN_PASSWORD: str = Field(default="changeme123")

    # JWT Authentication
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        description="Secret key for JWT encoding",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiry"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiry"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (e.g., redis://localhost:6379/0 or redis://:password@localhost:6379/0)",
    )

    # Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@restockr.ng")
    SMTP_FROM_NAME: str = Field(default="ReStockr Team")

    # Phone Validation
    DEFAULT_COUNTRY_CODE: str = Field(
        default="+234", description="Nigeria country code"
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://re-stockr.vercel.app",
        ]
    )

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=50)
    MAX_PAGE_SIZE: int = Field(default=500)


settings = Settings()
