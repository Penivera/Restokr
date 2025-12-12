from datetime import datetime, timedelta
from app.core.security import get_password_hash, generate_activation_token


def hash_password(plain_password: str) -> str:
    """Hash a password using the core security utility."""
    return get_password_hash(plain_password)


def generate_activation() -> tuple[str, datetime]:
    """Generate an activation token and expiry time (7 days)."""
    token = generate_activation_token()
    expiry = datetime.utcnow() + timedelta(days=7)
    return token, expiry


def extract_conflicting_field(db_error: str) -> str:
    """
    Extract the conflicting field from a database integrity error message.
    Works for common patterns in Postgres/MySQL/SQLite.
    """
    lower = db_error.lower()

    if "email" in lower:
        return "email"
    if "phone" in lower:
        return "phone_number"
    if "username" in lower:
        return "username"

    # fallback for unknown constraint
    return "field"
