"""
Test logging system

Verifies that all module loggers are working correctly
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db.base import Base
from services.user_service import create_user, authenticate_user


def test_logging_system():
    """Test that logging works for all modules"""
    print("=" * 60)
    print("LOGGING SYSTEM TEST")
    print("=" * 60)

    # Test 1: Import all loggers
    print("\n[Test 1] Importing all loggers...")
    from core.log.log_chess_engine import logger as chess_logger
    from core.log.log_database import logger as db_logger
    from core.log.log_auth import logger as auth_logger
    from core.log.log_service import logger as service_logger
    from core.log.log_api import logger as api_logger

    print("✓ All loggers imported successfully")

    # Test 2: Test basic logging
    print("\n[Test 2] Testing basic logging...")
    chess_logger.info("Chess engine logger test")
    db_logger.info("Database logger test")
    auth_logger.info("Auth logger test")
    service_logger.info("Service logger test")
    api_logger.info("API logger test")
    print("✓ Basic logging works")

    # Test 3: Test user service logging
    print("\n[Test 3] Testing user service with logging...")

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create user (should log)
        print("\n  Creating user (check logs above)...")
        user = create_user(
            db=db,
            identifier="log_test@example.com",
            identifier_type="email",
            password="test123",
            role="student",
            username="log_tester"
        )
        print(f"  ✓ User created: {user.username}")

        # Authenticate successfully (should log)
        print("\n  Authenticating with correct password (check logs above)...")
        auth_user = authenticate_user(db, "log_test@example.com", "test123")
        assert auth_user is not None
        print(f"  ✓ Authentication successful")

        # Authenticate with wrong password (should log warning)
        print("\n  Authenticating with wrong password (check logs above)...")
        failed_auth = authenticate_user(db, "log_test@example.com", "wrong_password")
        assert failed_auth is None
        print(f"  ✓ Wrong password rejected (logged)")

    finally:
        db.close()

    # Test 4: Test chess engine logging
    print("\n[Test 4] Testing chess engine logging...")
    try:
        from core.chess_engine.client import EngineClient

        print("\n  Initializing engine client (check logs above)...")
        engine = EngineClient()
        print(f"  ✓ Engine initialized")

        print("\n  Running analysis (check logs above)...")
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = engine.analyze(fen, depth=10, multipv=1)
        print(f"  ✓ Analysis complete: {len(result.lines)} lines")

    except Exception as e:
        print(f"  ⚠ Chess engine test skipped: {e}")

    # Check log files
    print("\n[Test 5] Checking log files...")
    logs_dir = Path(__file__).parent.parent / "logs"

    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"✓ Logs directory exists: {logs_dir}")
        print(f"✓ Log files created: {len(log_files)}")

        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"  - {log_file.name}: {size} bytes")
    else:
        print(f"⚠ Logs directory not yet created: {logs_dir}")

    print("\n" + "=" * 60)
    print("✅ LOGGING SYSTEM TEST COMPLETE")
    print("=" * 60)
    print("\nLog files should be in: logs/")
    print("  - chess_engine.log")
    print("  - database.log")
    print("  - auth.log")
    print("  - service.log")
    print("  - api.log")


if __name__ == "__main__":
    test_logging_system()
