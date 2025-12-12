from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.database import init_db, close_db
from app.core.redis import init_redis, close_redis
from app.config import settings
from app.api.v1 import admin, health, auth, users

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    await init_db()
    await init_redis()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_redis()
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

# Add custom middleware
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router, prefix=f"/api/{settings.API_PREFIX}", tags=["Authentication"]
)
app.include_router(users.router, prefix=f"/api/{settings.API_PREFIX}", tags=["User"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(health.router, tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to ReStockr Early Access API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "admin": {
            "stats": "/api/v1/admin/stats",
            "analytics": "/api/v1/admin/analytics",
            "export": "/api/v1/admin/export",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
