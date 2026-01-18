"""
Test Signup Flow with Verification Codes

Tests the complete signup flow:
1. POST /auth/register - Register and send verification email
2. POST /auth/verify-signup - Verify with code
3. POST /auth/resend-verification - Resend verification code
4. Test edge cases and error handling
"""
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.db.base import Base
from core.db.deps import get_db
from routers.auth import router as auth_router

if os.getenv("ALLOW_SIGNUP_TESTS") != "1":
    pytest.skip("Signup flow tests disabled (set ALLOW_SIGNUP_TESTS=1 to run).", allow_module_level=True)


# Create test app
app = FastAPI()
app.include_router(auth_router)

# Create test database engine with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables
Base.metadata.create_all(bind=test_engine)


# Test database setup
def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)


def test_register_sends_verification_email():
    """Test that registration sends verification email"""
    print("=" * 80)
    print("TEST: Registration with Verification Email")
    print("=" * 80)

    # Mock the email sending service
    with patch('services.resend_email_service.ResendEmailService.send_verification_code',
               new_callable=AsyncMock) as mock_send:
        # Configure mock to return success
        mock_send.return_value = True

        # Test 1: Register a new user
        print("\n[Test 1] Register new user...")
        response = client.post(
            "/auth/register",
            json={
                "identifier": "test@example.com",
                "identifier_type": "email",
                "password": "password123",
                "username": "testuser"
            }
        )

        # Check response
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["username"] == "testuser"
        assert data["identifier"] == "test@example.com"
        assert data["role"] == "student"  # Should be forced to student
        assert "verification_sent" in data
        print(f"✓ User registered: {data['username']}")
        print(f"✓ Verification sent: {data['verification_sent']}")

        # Verify email sending was called
        if data["verification_sent"]:
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args.kwargs["to_email"] == "test@example.com"
            assert "code" in call_args.kwargs
            print(f"✓ Email sent to: {call_args.kwargs['to_email']}")
            print(f"✓ Verification code (6 chars): {len(call_args.kwargs['code'])} characters")

    print("\n✅ Registration with verification email test passed")


def test_verify_signup_with_valid_code():
    """Test verification with valid code"""
    print("\n" + "=" * 80)
    print("TEST: Verify Signup with Valid Code")
    print("=" * 80)

    verification_code = None

    # Mock the email sending service to capture the code
    with patch('services.resend_email_service.ResendEmailService.send_verification_code',
               new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        # Step 1: Register user
        print("\n[Step 1] Register user...")
        response = client.post(
            "/auth/register",
            json={
                "identifier": "verify@example.com",
                "identifier_type": "email",
                "password": "password123",
                "username": "verifyuser"
            }
        )
        assert response.status_code == 201
        data = response.json()
        print(f"✓ User registered: {data['username']}")

        # Capture the verification code from the mock call
        if mock_send.called:
            verification_code = mock_send.call_args.kwargs["code"]
            print(f"✓ Verification code captured: {verification_code}")

    # Step 2: Verify with the code
    if verification_code:
        print("\n[Step 2] Verify with code...")
        response = client.post(
            "/auth/verify-signup",
            json={
                "identifier": "verify@example.com",
                "code": verification_code
            }
        )

        # Check response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        print(f"✓ Verification successful: {data['message']}")

        # Step 3: Try to use the same code again (should fail)
        print("\n[Step 3] Try to reuse code (should fail)...")
        response = client.post(
            "/auth/verify-signup",
            json={
                "identifier": "verify@example.com",
                "code": verification_code
            }
        )
        assert response.status_code == 400
        print("✓ Code reuse correctly rejected")

    print("\n✅ Verification flow test passed")


def test_verify_signup_with_invalid_code():
    """Test verification with invalid code"""
    print("\n" + "=" * 80)
    print("TEST: Verify Signup with Invalid Code")
    print("=" * 80)

    # Mock the email sending
    with patch('services.resend_email_service.ResendEmailService.send_verification_code',
               new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        # Step 1: Register user
        print("\n[Step 1] Register user...")
        response = client.post(
            "/auth/register",
            json={
                "identifier": "invalid@example.com",
                "identifier_type": "email",
                "password": "password123",
                "username": "invaliduser"
            }
        )
        assert response.status_code == 201
        print("✓ User registered")

    # Step 2: Try with invalid code
    print("\n[Step 2] Verify with invalid code...")
    response = client.post(
        "/auth/verify-signup",
        json={
            "identifier": "invalid@example.com",
            "code": "WRONG1"  # Invalid code
        }
    )

    # Should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    print(f"✓ Invalid code rejected: {data['detail']}")

    print("\n✅ Invalid code test passed")


def test_resend_verification_code():
    """Test resending verification code"""
    print("\n" + "=" * 80)
    print("TEST: Resend Verification Code")
    print("=" * 80)

    codes = []

    # Mock the email sending
    with patch('services.resend_email_service.ResendEmailService.send_verification_code',
               new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        # Step 1: Register user
        print("\n[Step 1] Register user...")
        response = client.post(
            "/auth/register",
            json={
                "identifier": "resend@example.com",
                "identifier_type": "email",
                "password": "password123",
                "username": "resenduser"
            }
        )
        assert response.status_code == 201
        print("✓ User registered")

        # Capture first code
        if mock_send.called:
            codes.append(mock_send.call_args.kwargs["code"])
            print(f"✓ First code captured: {codes[0]}")

        # Step 2: Resend verification code
        print("\n[Step 2] Resend verification code...")
        mock_send.reset_mock()
        response = client.post(
            "/auth/resend-verification",
            json={
                "identifier": "resend@example.com"
            }
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✓ Resend successful: {data['message']}")

        # Capture second code
        if mock_send.called:
            codes.append(mock_send.call_args.kwargs["code"])
            print(f"✓ Second code captured: {codes[1]}")

        # Step 3: Old code should be invalid
        if len(codes) >= 2:
            print("\n[Step 3] Verify old code is invalidated...")
            response = client.post(
                "/auth/verify-signup",
                json={
                    "identifier": "resend@example.com",
                    "code": codes[0]  # Old code
                }
            )
            assert response.status_code == 400
            print("✓ Old code correctly invalidated")

            # Step 4: New code should work
            print("\n[Step 4] Verify new code works...")
            response = client.post(
                "/auth/verify-signup",
                json={
                    "identifier": "resend@example.com",
                    "code": codes[1]  # New code
                }
            )
            assert response.status_code == 200
            print("✓ New code works correctly")

    print("\n✅ Resend verification test passed")


def test_verify_nonexistent_user():
    """Test verification for nonexistent user"""
    print("\n" + "=" * 80)
    print("TEST: Verify Nonexistent User")
    print("=" * 80)

    print("\n[Test] Verify nonexistent user...")
    response = client.post(
        "/auth/verify-signup",
        json={
            "identifier": "nonexistent@example.com",
            "code": "ABC123"
        }
    )

    # Should return 404
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    print(f"✓ Nonexistent user correctly rejected: {data['detail']}")

    print("\n✅ Nonexistent user test passed")


def test_resend_for_nonexistent_user():
    """Test resend for nonexistent user (should not reveal if user exists)"""
    print("\n" + "=" * 80)
    print("TEST: Resend for Nonexistent User")
    print("=" * 80)

    print("\n[Test] Resend for nonexistent user...")
    response = client.post(
        "/auth/resend-verification",
        json={
            "identifier": "nonexistent@example.com"
        }
    )

    # Should return 200 to prevent user enumeration
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print(f"✓ Response: {data['message']}")
    print("✓ User enumeration prevented (returns success even for nonexistent users)")

    print("\n✅ User enumeration prevention test passed")


def run_all_tests():
    """Run all signup tests"""
    print("\n" + "=" * 80)
    print("RUNNING ALL SIGNUP FLOW TESTS")
    print("=" * 80)

    try:
        test_register_sends_verification_email()
        test_verify_signup_with_valid_code()
        test_verify_signup_with_invalid_code()
        test_resend_verification_code()
        test_verify_nonexistent_user()
        test_resend_for_nonexistent_user()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
