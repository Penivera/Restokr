import secrets
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db

security = HTTPBasic()


async def verify_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
) -> HTTPBasicCredentials:
    """
    Verify admin credentials using HTTP Basic Auth.
    
    Args:
        credentials: HTTP Basic Auth credentials from request header
        
    Returns:
        Validated credentials
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Use constant-time comparison to prevent timing attacks
    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.ADMIN_USERNAME.encode("utf-8")
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.ADMIN_PASSWORD.encode("utf-8")
    )
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials


# Type alias for admin dependency
AdminDep = Annotated[HTTPBasicCredentials, Depends(verify_admin)]

# Type alias for database session dependency
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
