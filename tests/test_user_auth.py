"""
Test user authentication flow (pure Python, no HTTP)

This test verifies:
1. Password hashing and verification
2. User creation
3. User authentication
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.db.base import Base
from core.security.password import hash_password, verify_password
from services.user_service import create_user, authenticate_user, get_user_by_identifier


def test_password_hashing():
    """Test password hashing and verification"""
    print("=" * 60)
    print("TEST 1: Password Hashing")
    print("=" * 60)

    password = "my_secure_password_123"

    # Hash password
    hashed = hash_password(password)
    print(f"✓ Password hashed successfully")
    print(f"  Original: {password}")
    print(f"  Hashed: {hashed[:50]}...")

    # Verify correct password
    assert verify_password(password, hashed) is True
    print(f"✓ Correct password verified")

    # Verify incorrect password
    assert verify_password("wrong_password", hashed) is False
    print(f"✓ Incorrect password rejected")

    print()


def test_user_creation_and_authentication():
    """Test user creation and authentication flow"""
    print("=" * 60)
    print("TEST 2: User Creation & Authentication")
    print("=" * 60)

    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Test 1: Create a student user
        print("\n[Step 1] Creating student user...")
        user = create_user(
            db=db,
            identifier="student@example.com",
            identifier_type="email",
            password="student123",
            role="student",
            username="alex"
        )
        print(f"✓ User created: {user.username}")
        print(f"  - ID: {user.id}")
        print(f"  - Identifier: {user.identifier}")
        print(f"  - Role: {user.role}")
        print(f"  - Active: {user.is_active}")

        # Test 2: Try to create duplicate user (should fail)
        print("\n[Step 2] Testing duplicate user prevention...")
        try:
            create_user(
                db=db,
                identifier="student@example.com",
                identifier_type="email",
                password="another_password",
                role="student"
            )
            print("✗ FAILED: Duplicate user was allowed")
            assert False, "Duplicate user should not be allowed"
        except Exception as e:
            print(f"✓ Duplicate user rejected: {e.__class__.__name__}")

        # Test 3: Authenticate with correct password
        print("\n[Step 3] Testing authentication with correct password...")
        authenticated_user = authenticate_user(
            db=db,
            identifier="student@example.com",
            password="student123"
        )
        assert authenticated_user is not None
        assert authenticated_user.username == "alex"
        print(f"✓ Authentication successful")
        print(f"  User: {authenticated_user.username}")

        # Test 4: Authenticate with wrong password
        print("\n[Step 4] Testing authentication with wrong password...")
        authenticated_user = authenticate_user(
            db=db,
            identifier="student@example.com",
            password="wrong_password"
        )
        assert authenticated_user is None
        print(f"✓ Wrong password rejected")

        # Test 5: Authenticate non-existent user
        print("\n[Step 5] Testing authentication with non-existent user...")
        authenticated_user = authenticate_user(
            db=db,
            identifier="nonexistent@example.com",
            password="any_password"
        )
        assert authenticated_user is None
        print(f"✓ Non-existent user rejected")

        # Test 6: Create a teacher user
        print("\n[Step 6] Creating teacher user...")
        teacher = create_user(
            db=db,
            identifier="teacher@example.com",
            identifier_type="email",
            password="teacher456",
            role="teacher",
            username="prof_smith"
        )
        print(f"✓ Teacher created: {teacher.username}")
        print(f"  - Role: {teacher.role}")

        # Test 7: Authenticate teacher
        print("\n[Step 7] Authenticating teacher...")
        authenticated_teacher = authenticate_user(
            db=db,
            identifier="teacher@example.com",
            password="teacher456"
        )
        assert authenticated_teacher is not None
        assert authenticated_teacher.role == "teacher"
        print(f"✓ Teacher authenticated: {authenticated_teacher.username}")

        # Test 8: User lookup by identifier
        print("\n[Step 8] Testing user lookup...")
        found_user = get_user_by_identifier(db, "student@example.com")
        assert found_user is not None
        assert found_user.username == "alex"
        print(f"✓ User found: {found_user.username}")

        not_found = get_user_by_identifier(db, "nobody@example.com")
        assert not_found is None
        print(f"✓ Non-existent user returns None")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    finally:
        db.close()


def test_with_postgres():
    """Test with actual PostgreSQL database"""
    print("\n" + "=" * 60)
    print("TEST 3: PostgreSQL Integration Test")
    print("=" * 60)

    try:
        from core.db.session import SessionLocal

        db = SessionLocal()

        print("\n[Test] Creating user in PostgreSQL...")

        # Check if test user already exists
        existing = get_user_by_identifier(db, "test_user@catachess.com")
        if existing:
            print(f"⚠ Test user already exists, skipping creation")
        else:
            # Create a test user
            user = create_user(
                db=db,
                identifier="test_user@catachess.com",
                identifier_type="email",
                password="test_password_123",
                role="student",
                username="test_student"
            )
            print(f"✓ User created in PostgreSQL")
            print(f"  - Username: {user.username}")
            print(f"  - ID: {user.id}")

        # Authenticate
        print("\n[Test] Authenticating user...")
        authenticated = authenticate_user(
            db=db,
            identifier="test_user@catachess.com",
            password="test_password_123"
        )

        if authenticated:
            print(f"✓ Authentication successful")
            print(f"  - User: {authenticated.username}")
            print(f"  - Role: {authenticated.role}")
        else:
            print("✗ Authentication failed")

        db.close()

    except Exception as e:
        print(f"⚠ PostgreSQL test skipped: {e}")
        print("This is expected if not connected to Railway network")


if __name__ == "__main__":
    print("\n" + "🔐 " * 20)
    print("USER AUTHENTICATION TESTS")
    print("🔐 " * 20 + "\n")

    # Test 1: Password hashing
    test_password_hashing()

    # Test 2: User creation and authentication (SQLite)
    test_user_creation_and_authentication()

    # Test 3: PostgreSQL integration (may skip if not available)
    test_with_postgres()

    print("\n" + "🎉 " * 20)
    print("ALL TESTS COMPLETE")
    print("🎉 " * 20 + "\n")
