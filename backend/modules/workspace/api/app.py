"""
Main FastAPI application.
"""

from fastapi import FastAPI

from core.config import settings
from modules.workspace.db.session import init_db as init_workspace_db

from modules.workspace.api.router import api_router

app = FastAPI(title="CataChess Workspace API", version="1.0.0")

# Include main API router
app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize workspace database configuration."""
    workspace_db_url = settings.DATABASE_URL
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
