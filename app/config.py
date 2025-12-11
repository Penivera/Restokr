from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = Field(default="ReStockr Early Access API")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = Field(
        default="Hyper-local restocking platform - Early Access signup system"
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
