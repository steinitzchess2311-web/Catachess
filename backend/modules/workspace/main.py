"""
Main FastAPI application for workspace module.

This is a standalone app for development/testing.
In production, import api_router and mount it to main app.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Add backend directory to path to import from core modules
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.config import settings
from modules.workspace.api.router import api_router
from modules.workspace.db.session import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Workspace API",
    description="Chess study workspace management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
# SECURITY FIX: Cannot use allow_origins=["*"] with allow_credentials=True
# This is both insecure and incompatible with browsers
origins = settings.cors_origins_list
allow_credentials = True
if "*" in origins:
    origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins from config
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount workspace API router
app.include_router(api_router, prefix="/api/v1/workspace", tags=["workspace"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting workspace API...")
    # Note: Tables should be created via Alembic migrations
    # This is just for logging
    logger.info("Database engine initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down workspace API...")
    await engine.dispose()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "workspace"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Workspace API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
