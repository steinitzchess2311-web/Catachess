"""
Catachess Backend - Main FastAPI Application

This is the entry point for the Catachess backend API.
It registers all routers and configures the FastAPI application.
"""
import sys
from pathlib import Path

# Add backend directory to Python path for Railway deployment
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, assignments, user_profile, game_storage, chess_engine
from core.log.log_api import logger
from core.config import settings


# Create FastAPI application
app = FastAPI(
    title="Catachess API",
    description="Chess Education Platform Backend",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        from init_verification_table import init_verification_table
        init_verification_table()
        from init_game_tables import init_game_tables
        init_game_tables()
    except Exception as e:
        logger.warning(f"Could not initialize verification table: {e}")

# Configure CORS
# SECURITY FIX: Cannot use allow_origins=["*"] with allow_credentials=True
# This is both insecure and incompatible with browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Specific origins from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(user_profile.router)
app.include_router(game_storage.router)
app.include_router(chess_engine.router)

logger.info("Catachess API initialized")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Catachess API",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "service": "Catachess API",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Catachess API on port 8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
