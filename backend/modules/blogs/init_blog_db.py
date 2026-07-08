"""
Initialize Blog Database

This script creates the blog tables in the database using Alembic migrations.
Run this after deploying to Railway or setting up local environment.

Usage:
    python -m backend.modules.blogs.init_blog_db
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command


def init_blog_database():
    """Initialize blog database tables using Alembic migrations."""

    # Check for BLOG_DATABASE_URL
    blog_db_url = os.getenv("BLOG_DATABASE_URL")
    if not blog_db_url:
        print("❌ Error: BLOG_DATABASE_URL not set!")
        print("\nPlease set the environment variable:")
        print("export BLOG_DATABASE_URL=postgresql://...")
        sys.exit(1)

    print("🔧 Initializing Blog Database...")
    print(f"📍 Database: {blog_db_url.split('@')[1] if '@' in blog_db_url else 'localhost'}")

    # Create Alembic config
    alembic_ini_path = backend_dir / "alembic.ini"
    if not alembic_ini_path.exists():
        print(f"❌ Error: alembic.ini not found at {alembic_ini_path}")
        sys.exit(1)

    # Configure Alembic
    alembic_cfg = Config(str(alembic_ini_path))
    # Alembic stores options in ConfigParser, where percent-encoded passwords
    # must be escaped to avoid interpolation errors.
    alembic_cfg.set_main_option("sqlalchemy.url", blog_db_url.replace("%", "%%"))

    try:
        print("\n📋 Running database migrations...")

        # Upgrade to latest version
        command.upgrade(alembic_cfg, "head")

        print("\n✅ Blog database initialized successfully!")
        print("\n📊 Created tables:")
        print("  - blog_articles")
        print("  - blog_categories")
        print("\n📝 Initial categories inserted:")
        print("  - about (About Us)")
        print("  - function (Function Intro)")
        print("  - allblogs (All Blogs)")
        print("  - user (Users' Blogs)")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    init_blog_database()
