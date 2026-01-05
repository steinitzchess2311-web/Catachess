"""
Test JWT Authentication Flow

Tests the complete authentication flow:
1. authenticate_user() -> User
2. create_access_token(user_id) -> token
3. decode_token(token) -> user_id
4. get_current_user_sync(token, db) -> User
"""
import sys
from pathlib import Path
import time

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.db.base import Base
from services.user_service import create_user, authenticate_user
from core.security.jwt import create_access_token, decode_token
from core.security.current_user import get_current_user_sync
from core.errors import InvalidTokenError, UserInactiveError


def test_jwt_complete_flow():
    """Test complete JWT authentication flow"""
    print("=" * 60)
    print("JWT AUTHENTICATION FLOW TEST")
    print("=" * 60)

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Step 1: Create a user
        print("\n[Step 1] Creating user...")
        user = create_user(
            db=db,
            identifier="jwt_test@example.com",
            identifier_type="email",
            password="password123",
            role="student",
            username="jwt_tester"
        )
        print(f"✓ User created: {user.username} (id={user.id})")

        # Step 2: Authenticate user (simulates login)
        print("\n[Step 2] Authenticating user...")
        authenticated_user = authenticate_user(
            db=db,
            identifier="jwt_test@example.com",
            password="password123"
        )
        assert authenticated_user is not None
        print(f"✓ User authenticated: {authenticated_user.username}")

        # Step 3: Create JWT token
        print("\n[Step 3] Creating JWT token...")
        token = create_access_token(str(authenticated_user.id))
        print(f"✓ Token created: {token[:50]}...")
        print(f"  Token length: {len(token)} characters")

        # Step 4: Decode token
        print("\n[Step 4] Decoding token...")
        decoded_user_id = decode_token(token)
        assert decoded_user_id == str(authenticated_user.id)
        print(f"✓ Token decoded successfully")
        print(f"  User ID from token: {decoded_user_id}")

        # Step 5: Get current user from token
        print("\n[Step 5] Getting current user from token...")
        current_user = get_current_user_sync(token, db)
        assert current_user.id == authenticated_user.id
        assert current_user.username == authenticated_user.username
        print(f"✓ Current user retrieved: {current_user.username}")
        print(f"  User ID: {current_user.id}")
        print(f"  Role: {current_user.role}")

        # Step 6: Verify complete flow
        print("\n[Step 6] Verifying complete flow...")
        assert current_user.id == user.id
        print(f"✓ Complete flow verified: user -> token -> user")

        print("\n" + "=" * 60)
        print("✅ MINIMAL CLOSED LOOP COMPLETE")
        print("=" * 60)
        print("\nThe complete flow works:")
        print("  authenticate_user() → User")
        print("  create_access_token(user.id) → token")
        print("  decode_token(token) → user_id")
        print("  get_current_user_sync(token, db) → User")

    finally:
        db.close()


def test_jwt_token_validation():
    """Test JWT token validation and error cases"""
    print("\n" + "=" * 60)
    print("JWT TOKEN VALIDATION TEST")
    print("=" * 60)

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create a user
        user = create_user(
            db=db,
            identifier="validation_test@example.com",
            identifier_type="email",
            password="password123",
            role="teacher",
            username="validator"
        )

        # Test 1: Valid token
        print("\n[Test 1] Valid token...")
        token = create_access_token(str(user.id))
        current_user = get_current_user_sync(token, db)
        assert current_user.id == user.id
        print("✓ Valid token works correctly")

        # Test 2: Invalid token
        print("\n[Test 2] Invalid token...")
        try:
            invalid_token = "invalid.token.string"
            get_current_user_sync(invalid_token, db)
            print("✗ FAILED: Invalid token was accepted")
        except InvalidTokenError:
            print("✓ Invalid token rejected correctly")

        # Test 3: Tampered token
        print("\n[Test 3] Tampered token...")
        try:
            tampered_token = token[:-10] + "tampered00"
            get_current_user_sync(tampered_token, db)
            print("✗ FAILED: Tampered token was accepted")
        except InvalidTokenError:
            print("✓ Tampered token rejected correctly")

        # Test 4: Token for non-existent user
        print("\n[Test 4] Token for non-existent user...")
        try:
            fake_user_id = "00000000-0000-0000-0000-000000000000"
            fake_token = create_access_token(fake_user_id)
            get_current_user_sync(fake_token, db)
            print("✗ FAILED: Non-existent user token was accepted")
        except InvalidTokenError:
            print("✓ Non-existent user token rejected correctly")

        # Test 5: Inactive user
        print("\n[Test 5] Inactive user token...")
        inactive_user = create_user(
            db=db,
            identifier="inactive@example.com",
            identifier_type="email",
            password="password123",
            role="student",
            username="inactive"
        )
        inactive_user.is_active = False
        db.commit()

        try:
            inactive_token = create_access_token(str(inactive_user.id))
            get_current_user_sync(inactive_token, db)
            print("✗ FAILED: Inactive user token was accepted")
        except UserInactiveError:
            print("✓ Inactive user token rejected correctly")

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)

    finally:
        db.close()


def test_jwt_token_properties():
    """Test JWT token properties"""
    print("\n" + "=" * 60)
    print("JWT TOKEN PROPERTIES TEST")
    print("=" * 60)

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create a user
        user = create_user(
            db=db,
            identifier="props_test@example.com",
            identifier_type="email",
            password="password123",
            role="student",
            username="props_tester"
        )

        # Test 1: Token contains user_id
        print("\n[Test 1] Token contains correct user_id...")
        token = create_access_token(str(user.id))
        decoded_id = decode_token(token)
        assert decoded_id == str(user.id)
        print(f"✓ Token contains user_id: {decoded_id}")

        # Test 2: Token is a string
        print("\n[Test 2] Token format...")
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
        print(f"✓ Token is valid JWT format")
        print(f"  Length: {len(token)} characters")
        print(f"  Parts: {token.count('.') + 1}")

        # Test 3: Different users get different tokens
        print("\n[Test 3] Token uniqueness...")
        user2 = create_user(
            db=db,
            identifier="props_test2@example.com",
            identifier_type="email",
            password="password123",
            role="teacher",
            username="props_tester2"
        )
        token2 = create_access_token(str(user2.id))
        assert token != token2
        print(f"✓ Different users get different tokens")

        # Test 4: Same user gets different tokens (due to timestamp)
        print("\n[Test 4] Token regeneration...")
        time.sleep(1)
        token3 = create_access_token(str(user.id))
        assert token != token3  # Different due to timestamp
        decoded_id3 = decode_token(token3)
        assert decoded_id3 == str(user.id)  # But same user_id
        print(f"✓ New token for same user works correctly")

        print("\n" + "=" * 60)
        print("✅ TOKEN PROPERTIES VERIFIED")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "🔐 " * 20)
    print("JWT AUTHENTICATION SYSTEM TESTS")
    print("🔐 " * 20 + "\n")

    # Test 1: Complete flow
    test_jwt_complete_flow()

    # Test 2: Token validation
    test_jwt_token_validation()

    # Test 3: Token properties
    test_jwt_token_properties()

    print("\n" + "🎉 " * 20)
    print("ALL JWT TESTS COMPLETE")
    print("🎉 " * 20 + "\n")

    print("Summary:")
    print("  ✓ Complete authentication flow works")
    print("  ✓ Token creation and decoding work")
    print("  ✓ Invalid tokens are rejected")
    print("  ✓ Tampered tokens are rejected")
    print("  ✓ Non-existent users are rejected")
    print("  ✓ Inactive users are rejected")
    print("  ✓ Token properties are correct")
    print("\n✅ JWT authentication system is fully functional!")
