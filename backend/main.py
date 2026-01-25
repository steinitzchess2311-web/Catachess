"""
Catachess Backend - Main FastAPI Application

This is the entry point for the Catachess backend API.
It registers all routers and configures the FastAPI application.
"""
import sys
from pathlib import Path

# Add backend directory to Python path for Railway deployment
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(1, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, assignments, user_profile, game_storage, chess_engine, chess_rules, imitator, tagger_router
from modules.workspace.api.router import api_router as workspace_router
from core.log.log_api import logger
from core.config import settings
from modules.workspace.db.session import init_db as init_workspace_db


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
        workspace_db_url = settings.DATABASE_URL
        if not workspace_db_url:
            logger.warning("Workspace DATABASE_URL not set. Skipping workspace database initialization.")
        else:
            redacted_url = workspace_db_url
            if "://" in redacted_url and "@" in redacted_url:
                scheme, rest = redacted_url.split("://", 1)
                credentials, host = rest.split("@", 1)
                if ":" in credentials:
                    user, _ = credentials.split(":", 1)
                    credentials = f"{user}:***"
                redacted_url = f"{scheme}://{credentials}@{host}"
            logger.info(f"Workspace DATABASE_URL resolved: {redacted_url}")

            if workspace_db_url.startswith("postgresql://"):
                workspace_db_url = workspace_db_url.replace(
                    "postgresql://",
                    "postgresql+asyncpg://",
                    1,
                )
            elif workspace_db_url.startswith("sqlite://"):
                workspace_db_url = workspace_db_url.replace(
                    "sqlite://",
                    "sqlite+aiosqlite://",
                    1,
                )
            init_workspace_db(workspace_db_url, echo=settings.DEBUG)
            logger.info("Workspace database initialized")
    except Exception as e:
        logger.error(f"Workspace database init failed: {e}", exc_info=True)

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
origins = settings.cors_origins_list
origin_regex = settings.CORS_ORIGIN_REGEX or None
allow_credentials = True
for extra_origin in (
    "https://catachess.com",
    "https://www.catachess.com",
    "https://catachess.com.",
    "https://www.catachess.com.",
):
    if extra_origin not in origins:
        origins.append(extra_origin)
if "https://catachess.com" not in origins:
    origins.append("https://catachess.com")
if "https://www.catachess.com" not in origins:
    origins.append("https://www.catachess.com")
if "*" in origins:
    origins = ["*"]
    allow_credentials = False
if not origins and not origin_regex:
    origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins from config
    allow_origin_regex=origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(user_profile.router)
app.include_router(game_storage.router)
app.include_router(chess_engine.router)
app.include_router(chess_rules.router)
app.include_router(imitator.router)
app.include_router(tagger_router)
app.include_router(workspace_router, prefix="/api/v1/workspace", tags=["workspace"])

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
