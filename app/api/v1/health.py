from datetime import datetime
from fastapi import APIRouter, status
from sqlalchemy import text
from app.api.deps import DBSessionDep
from app.config import settings

router = APIRouter(prefix="/api/v1/health")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check system health and database connectivity"
)
async def health_check(db: DBSessionDep) -> dict:
    """
    Comprehensive health check endpoint.
    
    Returns:
        - System status
        - Database connectivity
        - Timestamp
        - Version
    """
    db_status = "healthy"
    db_message = "Connected"
    
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        
        # Test PostGIS extension
        result = await db.execute(text("SELECT PostGIS_version()"))
        postgis_version = result.scalar_one()
        db_message = f"Connected (PostGIS: {postgis_version})"
        
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "database": {
            "status": db_status,
            "message": db_message
        }
    }


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="Simple Ping",
    description="Lightweight health check without database connection"
)
async def ping() -> dict:
    """
    Simple ping endpoint for basic uptime monitoring.
    
    Does not check database connectivity.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "pong"
    }
