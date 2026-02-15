"""
Catachess Backend - Main FastAPI Application

This is the entry point for the Catachess backend API.
It registers all routers and configures the FastAPI application.
"""
import asyncio
import re
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend directory to Python path for Railway deployment
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(1, str(project_root))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, assignments, user_profile, game_storage, chess_engine, chess_rules, imitator, tagger_router, blog_admin
from modules.workspace.api.router import api_router as workspace_router
from modules.blogs.api.router import router as blog_router
from core.log.log_api import logger
from core.config import settings
from modules.workspace.db.session import init_db as init_workspace_db


async def _init_workspace_db() -> None:
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

async def _init_blog_db() -> None:
    """Initialize blog database and run migrations if needed"""
    import os
    from sqlalchemy import create_engine, text, inspect

    try:
        # Blog module uses the main DATABASE_URL (not BLOG_DATABASE_URL)
        blog_db_url = os.getenv("BLOG_DATABASE_URL") or settings.DATABASE_URL
        if not blog_db_url:
            logger.warning("DATABASE_URL not set. Skipping blog database initialization.")
            return

        logger.info("Checking blog database...")
        engine = create_engine(blog_db_url)
        inspector = inspect(engine)

        # Check what tables exist
        tables = inspector.get_table_names()
        needs_base_tables = 'blog_articles' not in tables or 'blog_images' not in tables
        needs_migration = False

        # Check if blog_article_images table exists
        if 'blog_images' in tables and 'blog_article_images' not in tables:
            logger.info("blog_article_images table not found - migration needed")
            needs_migration = True

        # Check if blog_articles has is_hidden field
        if 'blog_articles' in tables and not needs_migration:
            columns = inspector.get_columns('blog_articles')
            col_names = [col['name'] for col in columns]
            if 'is_hidden' not in col_names:
                logger.info("blog_articles missing is_hidden field - migration needed")
                needs_migration = True

        # Check if blog_images has new fields
        if 'blog_images' in tables and not needs_migration:
            columns = inspector.get_columns('blog_images')
            col_names = [col['name'] for col in columns]
            if 'is_orphan' not in col_names:
                logger.info("blog_images missing new fields - migration needed")
                needs_migration = True

        # Step 0: Create base tables if needed
        if needs_base_tables:
            logger.info("🔨 Creating blog base tables...")
            with engine.begin() as conn:
                # Create blog_articles table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS blog_articles (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title VARCHAR(200) NOT NULL,
                        subtitle TEXT,
                        content TEXT NOT NULL,
                        cover_image_url TEXT,

                        author_id UUID,
                        author_name VARCHAR(100) NOT NULL DEFAULT 'Chessortag Team',
                        author_type VARCHAR(20) NOT NULL DEFAULT 'official',

                        category VARCHAR(50) NOT NULL,
                        sub_category VARCHAR(50),
                        tags TEXT[],

                        status VARCHAR(20) NOT NULL DEFAULT 'draft',
                        is_pinned BOOLEAN NOT NULL DEFAULT false,
                        pin_order INTEGER NOT NULL DEFAULT 0,
                        is_hidden BOOLEAN NOT NULL DEFAULT false,

                        view_count INTEGER NOT NULL DEFAULT 0,
                        like_count INTEGER NOT NULL DEFAULT 0,
                        comment_count INTEGER NOT NULL DEFAULT 0,

                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        published_at TIMESTAMP,

                        CONSTRAINT blog_articles_status_check CHECK (status IN ('draft', 'published', 'archived')),
                        CONSTRAINT blog_articles_author_type_check CHECK (author_type IN ('official', 'user'))
                    );

                    CREATE INDEX IF NOT EXISTS ix_blog_articles_category ON blog_articles(category);
                    CREATE INDEX IF NOT EXISTS ix_blog_articles_status ON blog_articles(status);
                    CREATE INDEX IF NOT EXISTS ix_blog_articles_published_at ON blog_articles(published_at);
                    CREATE INDEX IF NOT EXISTS ix_blog_articles_is_hidden ON blog_articles(is_hidden);
                """))

                # Create blog_images table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS blog_images (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        filename VARCHAR(255) NOT NULL,
                        storage_path VARCHAR(500) NOT NULL,
                        url TEXT NOT NULL,
                        content_type VARCHAR(50) NOT NULL,

                        size_bytes INTEGER NOT NULL,
                        width INTEGER NOT NULL,
                        height INTEGER NOT NULL,

                        resize_mode VARCHAR(20) NOT NULL,
                        image_type VARCHAR(20) NOT NULL,

                        uploaded_by UUID,
                        article_id UUID,

                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),

                        CONSTRAINT blog_images_resize_mode_check CHECK (resize_mode IN ('original', 'adaptive_width')),
                        CONSTRAINT blog_images_image_type_check CHECK (image_type IN ('cover', 'content'))
                    );

                    CREATE INDEX IF NOT EXISTS ix_blog_images_article_id ON blog_images(article_id);
                    CREATE INDEX IF NOT EXISTS ix_blog_images_created_at ON blog_images(created_at);
                """))
            logger.info("✅ Blog base tables created")
            # Refresh table list
            tables = inspector.get_table_names()
            # Now we definitely need migration
            needs_migration = True

        if needs_migration:
            logger.info("🚀 Running blog database migration...")

            with engine.begin() as conn:
                # Step 0: Add is_hidden to blog_articles
                logger.info("  Adding is_hidden column to blog_articles...")
                conn.execute(text("""
                    ALTER TABLE blog_articles
                    ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT false;

                    CREATE INDEX IF NOT EXISTS ix_blog_articles_is_hidden ON blog_articles(is_hidden);
                """))

                # Step 1: Add new columns to blog_images
                logger.info("  Adding columns to blog_images...")
                conn.execute(text("""
                    ALTER TABLE blog_images
                    ADD COLUMN IF NOT EXISTS is_orphan BOOLEAN DEFAULT true,
                    ADD COLUMN IF NOT EXISTS marked_for_deletion_at TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS last_referenced_at TIMESTAMP;
                """))

                # Step 2: Create blog_article_images table
                logger.info("  Creating blog_article_images table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS blog_article_images (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        article_id UUID NOT NULL,
                        image_id UUID NOT NULL,
                        position INTEGER,
                        usage_context VARCHAR(20) NOT NULL DEFAULT 'content',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),

                        CONSTRAINT blog_article_images_usage_check
                        CHECK (usage_context IN ('content', 'cover')),

                        CONSTRAINT blog_article_images_unique
                        UNIQUE (article_id, image_id)
                    );
                """))

                # Step 3: Create indexes
                logger.info("  Creating indexes...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_article_images_article
                    ON blog_article_images(article_id);

                    CREATE INDEX IF NOT EXISTS idx_article_images_image
                    ON blog_article_images(image_id);
                """))

                # Step 4: Migrate existing data
                logger.info("  Migrating existing data...")
                conn.execute(text("""
                    INSERT INTO blog_article_images (article_id, image_id, usage_context, created_at)
                    SELECT
                        article_id,
                        id as image_id,
                        CASE
                            WHEN image_type = 'cover' THEN 'cover'
                            ELSE 'content'
                        END as usage_context,
                        created_at
                    FROM blog_images
                    WHERE article_id IS NOT NULL
                    ON CONFLICT (article_id, image_id) DO NOTHING;
                """))

                # Step 5: Update is_orphan status
                logger.info("  Updating orphan status...")
                conn.execute(text("""
                    UPDATE blog_images
                    SET is_orphan = CASE
                        WHEN article_id IS NOT NULL THEN false
                        ELSE true
                    END,
                    last_referenced_at = CASE
                        WHEN article_id IS NOT NULL THEN NOW()
                        ELSE NULL
                    END;
                """))

            logger.info("✅ Blog database migration completed successfully!")
        else:
            logger.info("✅ Blog database is up to date")

    except Exception as e:
        logger.error(f"Blog database initialization failed: {e}", exc_info=True)
        logger.warning("Blog module may not function correctly")


async def _presence_cleanup_loop() -> None:
    import os

    from modules.workspace.db.repos.presence_repo import PresenceRepository
    from modules.workspace.domain.services.presence_service import PresenceService
    from modules.workspace.events.bus import EventBus
    from modules.workspace.db.session import get_session

    interval_seconds = int(os.getenv("PRESENCE_CLEANUP_INTERVAL_SECONDS", "300"))
    timeout_minutes = int(os.getenv("PRESENCE_CLEANUP_TIMEOUT_MINUTES", "10"))

    while True:
        try:
            async for session in get_session():
                presence_repo = PresenceRepository(session)
                event_bus = EventBus(session)
                service = PresenceService(
                    session=session,
                    presence_repo=presence_repo,
                    event_bus=event_bus,
                )
                await service.cleanup_expired_sessions(timeout_minutes=timeout_minutes)
                break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(f"Presence cleanup loop error: {exc}", exc_info=True)
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_workspace_db()

    # Initialize Blog database and run migrations
    await _init_blog_db()

    # Initialize MongoDB cache
    try:
        from core.cache import get_mongo_cache
        await get_mongo_cache()
        logger.info("MongoDB cache initialized")
    except Exception as e:
        logger.warning(f"MongoDB cache initialization failed: {e}")

    # Initialize Engine Queue
    try:
        from core.chess_engine.queue import get_engine_queue
        engine_queue = get_engine_queue()
        logger.info(f"Engine queue initialized with {engine_queue._max_workers} workers")
    except Exception as e:
        logger.error(f"Engine queue initialization failed: {e}")

    tasks: list[asyncio.Task] = []
    if settings.DEBUG:
        logger.info("Starting background tasks (non-blocking)")
    if settings.ENABLE_PRESENCE_CLEANUP:
        tasks.append(asyncio.create_task(_presence_cleanup_loop()))
    try:
        yield
    finally:
        # Cleanup: Stop engine queue
        try:
            from core.chess_engine.queue import shutdown_engine_queue
            await shutdown_engine_queue()
            logger.info("Engine queue stopped")
        except Exception as e:
            logger.error(f"Engine queue cleanup failed: {e}")

        # Cleanup: Stop background tasks
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass


# Create FastAPI application
app = FastAPI(
    title="Catachess API",
    description="Chess Education Platform Backend",
    version="1.0.0",
    lifespan=lifespan,
)

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

def _tagger_cors_headers(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allowed = origin in origins
    if not allowed and origin_regex:
        try:
            allowed = re.match(origin_regex, origin) is not None
        except re.error:
            allowed = False
    if not allowed:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type",
        "Vary": "Origin",
    }


@app.middleware("http")
async def tagger_cors_failsafe(request: Request, call_next):
    # Only affects /api/tagger/* to avoid impacting other routes.
    if request.url.path.startswith("/api/tagger/"):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=_tagger_cors_headers(request))
        response = await call_next(request)
        headers = _tagger_cors_headers(request)
        if headers:
            response.headers.update(headers)
        return response
    return await call_next(request)


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
app.include_router(blog_admin.router)
app.include_router(blog_router)
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


@app.get("/api/metrics")
async def performance_metrics():
    """
    Performance metrics endpoint for monitoring system health

    Returns:
        - Database connection pool stats
        - Engine queue statistics
        - MongoDB cache statistics
    """
    metrics = {
        "service": "Catachess API",
        "timestamp": __import__("time").time(),
    }

    # Database pool metrics
    try:
        from core.db.db_engine import db_engine
        metrics["database"] = {
            "pool_size": db_engine.pool.size(),
            "checked_out_connections": db_engine.pool.checkedout(),
            "overflow_connections": db_engine.pool.overflow(),
            "pool_status": "healthy" if db_engine.pool.checkedout() < db_engine.pool.size() else "high_usage",
        }
    except Exception as e:
        metrics["database"] = {"error": str(e)}

    # Engine queue metrics
    try:
        from core.chess_engine.queue import get_engine_queue
        engine_queue = get_engine_queue()
        stats = engine_queue.get_stats()
        metrics["engine_queue"] = {
            "queue_size": stats.queue_size,
            "active_workers": stats.active_workers,
            "total_requests": stats.total_requests,
            "total_completed": stats.total_completed,
            "total_failed": stats.total_failed,
            "avg_wait_time_ms": round(stats.avg_wait_time_ms, 1),
            "avg_processing_time_ms": round(stats.avg_processing_time_ms, 1),
            "status": "healthy" if stats.queue_size < 10 else "high_queue",
        }
    except Exception as e:
        metrics["engine_queue"] = {"error": str(e)}

    # MongoDB cache metrics
    try:
        from core.cache import get_mongo_cache
        mongo_cache = await get_mongo_cache()
        cache_stats = await mongo_cache.get_stats()
        metrics["mongodb_cache"] = cache_stats
    except Exception as e:
        metrics["mongodb_cache"] = {"error": str(e)}

    return metrics


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
