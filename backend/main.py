"""
Catachess Backend - Main FastAPI Application

This is the entry point for the Catachess backend API.
It registers all routers and configures the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, assignments
from core.log.log_api import logger
from core.config import settings


# Create FastAPI application
app = FastAPI(
    title="Catachess API",
    description="Chess Education Platform Backend",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)
app.include_router(assignments.router)

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
