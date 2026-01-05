"""
Test Assignments API - Teacher-only Business Endpoint

This test verifies that the authentication and authorization system
works correctly in a real business context.

Tests:
- 401: Unauthenticated access is rejected
- 403: Student access to teacher-only endpoint is rejected
- 200: Teacher access works and returns correct data
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.db.base import Base
from core.db.deps import get_db
from routers.auth import router as auth_router
from routers.assignments import router as assignments_router
from models.user import User

# Create test app
app = FastAPI()
app.include_router(auth_router)
app.include_router(assignments_router)

# Create a single test database engine with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables
Base.metadata.create_all(bind=test_engine)


def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)


def test_assignments_authentication():
    """Test authentication requirements for assignments endpoint"""
    print("=" * 60)
    print("TEST: Assignments API Authentication & Authorization")
    print("=" * 60)

    # Setup: Create teacher and student users
    print("\n[Setup] Creating teacher and student accounts...")

    teacher_response = client.post(
        "/auth/register",
        json={
            "identifier": "teacher_assign@test.com",
            "password": "password123",
            "role": "teacher",
            "username": "assign_teacher"
        }
    )
    assert teacher_response.status_code == 201
    print(f"✓ Teacher registered: assign_teacher")

    student_response = client.post(
        "/auth/register",
        json={
            "identifier": "student_assign@test.com",
            "password": "password123",
            "role": "student",
            "username": "assign_student"
        }
    )
    assert student_response.status_code == 201
    print(f"✓ Student registered: assign_student")

    # Get tokens
    teacher_login = client.post(
        "/auth/login/json",
        json={"identifier": "teacher_assign@test.com", "password": "password123"}
    )
    teacher_token = teacher_login.json()["access_token"]
    print(f"✓ Teacher token obtained: {teacher_token[:30]}...")

    student_login = client.post(
        "/auth/login/json",
        json={"identifier": "student_assign@test.com", "password": "password123"}
    )
    student_token = student_login.json()["access_token"]
    print(f"✓ Student token obtained: {student_token[:30]}...")

    # Test 1: No authentication - should return 401
    print("\n[Test 1] Accessing /assignments without token...")
    response = client.post(
        "/assignments/",
        json={"title": "Test Assignment", "description": "Test"}
    )
    assert response.status_code == 401
    print("✓ 401 Unauthorized - No token rejected correctly")

    # Test 2: Invalid token - should return 401
    print("\n[Test 2] Accessing /assignments with invalid token...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": "Bearer invalid_token_here"},
        json={"title": "Test Assignment", "description": "Test"}
    )
    assert response.status_code == 401
    print("✓ 401 Unauthorized - Invalid token rejected correctly")

    # Test 3: Student token - should return 403 (authenticated but not authorized)
    print("\n[Test 3] Student accessing teacher-only endpoint...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Test Assignment", "description": "Student trying"}
    )
    assert response.status_code == 403
    data = response.json()
    assert "Teacher" in data["detail"] or "teacher" in data["detail"]
    print("✓ 403 Forbidden - Student denied access to teacher endpoint")

    # Test 4: Teacher token - should return 200 with correct data
    print("\n[Test 4] Teacher accessing endpoint...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"title": "Checkmate Patterns", "description": "Learn basic checkmate patterns"}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["ok"] is True
    assert "teacher_id" in data
    assert data["teacher_username"] == "assign_teacher"
    assert data["assignment"]["title"] == "Checkmate Patterns"
    assert data["assignment"]["description"] == "Learn basic checkmate patterns"

    print(f"✓ 200 OK - Teacher access granted")
    print(f"  Teacher ID: {data['teacher_id']}")
    print(f"  Teacher Username: {data['teacher_username']}")
    print(f"  Assignment: {data['assignment']['title']}")

    # Test 5: Teacher accessing GET endpoint
    print("\n[Test 5] Teacher listing assignments...")
    response = client.get(
        "/assignments/",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["teacher_username"] == "assign_teacher"
    assert "assignments" in data
    print(f"✓ 200 OK - Teacher can list assignments")

    # Test 6: Student accessing GET endpoint - should also be 403
    print("\n[Test 6] Student trying to list assignments...")
    response = client.get(
        "/assignments/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403
    print("✓ 403 Forbidden - Student denied access to list endpoint")

    print("\n✅ All assignments API tests passed")


def test_assignments_data_validation():
    """Test that assignment data is properly validated"""
    print("\n" + "=" * 60)
    print("TEST: Assignments Data Validation")
    print("=" * 60)

    # Setup: Create teacher and get token
    client.post(
        "/auth/register",
        json={
            "identifier": "teacher_data@test.com",
            "password": "password123",
            "role": "teacher",
            "username": "data_teacher"
        }
    )

    teacher_login = client.post(
        "/auth/login/json",
        json={"identifier": "teacher_data@test.com", "password": "password123"}
    )
    teacher_token = teacher_login.json()["access_token"]

    # Test 1: Missing required field
    print("\n[Test 1] Creating assignment without title...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"description": "No title provided"}
    )
    assert response.status_code == 422  # Validation error
    print("✓ 422 Unprocessable Entity - Missing title rejected")

    # Test 2: Valid minimal data (title only)
    print("\n[Test 2] Creating assignment with title only...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"title": "Minimal Assignment"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assignment"]["title"] == "Minimal Assignment"
    assert data["assignment"]["description"] is None
    print("✓ 200 OK - Minimal valid data accepted")

    # Test 3: Valid complete data
    print("\n[Test 3] Creating assignment with all fields...")
    response = client.post(
        "/assignments/",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "title": "Complete Assignment",
            "description": "This has all fields"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assignment"]["title"] == "Complete Assignment"
    assert data["assignment"]["description"] == "This has all fields"
    print("✓ 200 OK - Complete data accepted")

    print("\n✅ Data validation tests passed")


if __name__ == "__main__":
    print("\n" + "📝 " * 20)
    print("ASSIGNMENTS API TESTS")
    print("📝 " * 20 + "\n")

    # Run tests
    test_assignments_authentication()
    test_assignments_data_validation()

    print("\n" + "🎉 " * 20)
    print("ALL ASSIGNMENTS API TESTS COMPLETE")
    print("🎉 " * 20 + "\n")

    print("Summary:")
    print("  ✓ 401: No authentication rejected")
    print("  ✓ 401: Invalid token rejected")
    print("  ✓ 403: Student access to teacher endpoint rejected")
    print("  ✓ 200: Teacher access granted with correct data")
    print("  ✓ Teacher can access both POST and GET endpoints")
    print("  ✓ Data validation works correctly")
    print("\n✅ Authentication & Authorization verified in business context!")
