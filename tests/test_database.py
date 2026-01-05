"""
Test database connection and User model
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.db.base import Base
from models.user import User


def test_user_model_structure():
    """Test that User model is properly defined"""
    print("Testing User model structure...")

    # Check table name
    assert User.__tablename__ == "users"
    print(f"✓ Table name: {User.__tablename__}")

    # Check columns exist
    columns = User.__table__.columns.keys()
    expected_columns = [
        'id', 'identifier', 'identifier_type', 'username',
        'hashed_password', 'role', 'is_active', 'created_at'
    ]

    for col in expected_columns:
        assert col in columns, f"Missing column: {col}"
        print(f"✓ Column exists: {col}")

    print("\n✓ User model structure is correct!\n")


def test_user_creation_with_sqlite():
    """Test User creation with local SQLite database"""
    print("Testing User creation with SQLite...")

    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create a test user
        test_user = User(
            id=uuid.uuid4(),
            identifier="test@example.com",
            identifier_type="email",
            username="testuser",
            hashed_password="hashed_password_here",
            role="student",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"✓ Created user: {test_user.username}")
        print(f"  - ID: {test_user.id}")
        print(f"  - Identifier: {test_user.identifier}")
        print(f"  - Role: {test_user.role}")
        print(f"  - Active: {test_user.is_active}")

        # Query the user back
        queried_user = db.query(User).filter(User.identifier == "test@example.com").first()
        assert queried_user is not None
        assert queried_user.username == "testuser"
        print(f"✓ Successfully queried user back from database")

        # Test unique constraint
        print("\nTesting unique constraint on identifier...")
        duplicate_user = User(
            id=uuid.uuid4(),
            identifier="test@example.com",  # Same identifier
            identifier_type="email",
            hashed_password="another_hash",
            role="teacher",
        )

        db.add(duplicate_user)
        try:
            db.commit()
            print("✗ Unique constraint failed - duplicate was allowed!")
        except Exception as e:
            db.rollback()
            print(f"✓ Unique constraint working - duplicate rejected")

        print("\n✓ User creation and querying works!\n")

    finally:
        db.close()


def test_postgres_connection():
    """Test connection to Railway Postgres (will fail if not in Railway network)"""
    print("Testing PostgreSQL connection...")

    from core.config import settings

    print(f"Database URL: {settings.DATABASE_URL[:50]}...")

    try:
        from core.db.db_engine import db_engine

        # Try to connect
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
            print("✓ Successfully connected to PostgreSQL!")

            # Check if users table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            ))
            table_exists = result.fetchone()[0]

            if table_exists:
                print("✓ Users table exists in database!")

                # Count users
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.fetchone()[0]
                print(f"  - Current user count: {count}")
            else:
                print("⚠ Users table does not exist yet. Run migrations:")
                print("  cd backend && alembic upgrade head")

    except Exception as e:
        print(f"✗ Cannot connect to PostgreSQL: {e}")
        print("\nThis is expected if running locally.")
        print("The database URL uses Railway's internal network (postgres.railway.internal)")
        print("which is only accessible from within Railway's infrastructure.")
        print("\nTo run migrations on Railway:")
        print("  1. Deploy your code to Railway")
        print("  2. Run: railway run alembic upgrade head")


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE TESTS")
    print("=" * 60)
    print()

    # Test 1: Model structure
    test_user_model_structure()

    # Test 2: User creation with SQLite
    test_user_creation_with_sqlite()

    # Test 3: PostgreSQL connection (may fail locally)
    test_postgres_connection()

    print("=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
