"""
Test Auth API Endpoints

Tests the complete HTTP authentication flow:
- POST /auth/register - User registration
- POST /auth/login - User login (OAuth2 form)
- POST /auth/login/json - User login (JSON)
- Protected endpoints with authentication
- Protected endpoints with authorization (teacher/student)
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.db.base import Base
from core.db.deps import get_db
from routers.auth import router as auth_router
from core.security.deps import get_teacher_user, get_student_user
from models.user import User

# Create test app
app = FastAPI()
app.include_router(auth_router)

# Add protected test endpoints
@app.get("/test/me")
def test_me(user: User = Depends(get_db)):
    from core.security.current_user import get_current_user
    user = get_current_user(token="dummy", db=user)
    return {"username": user.username, "role": user.role}


@app.get("/test/teacher-only")
def test_teacher_only(teacher: User = Depends(get_teacher_user)):
    return {"message": "teacher access granted", "teacher": teacher.username}


@app.get("/test/student-only")
def test_student_only(student: User = Depends(get_student_user)):
    return {"message": "student access granted", "student": student.username}


# Create a single test database engine with StaticPool
# StaticPool ensures all connections use the same in-memory database
test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # This is the key fix!
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables
Base.metadata.create_all(bind=test_engine)


# Test database setup - returns same database for all requests
def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)


def test_registration():
    """Test user registration endpoint"""
    print("=" * 60)
    print("TEST: User Registration")
    print("=" * 60)

    # Test 1: Register a student
    print("\n[Test 1] Register student...")
    response = client.post(
        "/auth/register",
        json={
            "identifier": "student@test.com",
            "password": "password123",
            "role": "student",
            "username": "test_student"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_student"
    assert data["role"] == "student"
    assert data["identifier"] == "student@test.com"
    assert "id" in data
    print(f"✓ Student registered: {data['username']}")

    # Test 2: Register a teacher
    print("\n[Test 2] Register teacher...")
    response = client.post(
        "/auth/register",
        json={
            "identifier": "teacher@test.com",
            "password": "password456",
            "role": "teacher",
            "username": "test_teacher"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "teacher"
    print(f"✓ Teacher registered: {data['username']}")

    # Test 3: Duplicate registration (should fail)
    print("\n[Test 3] Duplicate registration...")
    response = client.post(
        "/auth/register",
        json={
            "identifier": "student@test.com",
            "password": "different",
            "role": "student"
        }
    )
    assert response.status_code == 409
    print("✓ Duplicate registration rejected correctly")

    print("\n✅ Registration tests passed")


def test_login():
    """Test user login endpoints"""
    print("\n" + "=" * 60)
    print("TEST: User Login")
    print("=" * 60)

    # Setup: Register a user
    client.post(
        "/auth/register",
        json={
            "identifier": "login_test@test.com",
            "password": "password123",
            "role": "student",
            "username": "login_tester"
        }
    )

    # Test 1: Login with form data (OAuth2)
    print("\n[Test 1] Login with OAuth2 form...")
    response = client.post(
        "/auth/login",
        data={
            "username": "login_test@test.com",  # OAuth2 uses 'username' field
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    token = data["access_token"]
    print(f"✓ Login successful, token received: {token[:30]}...")

    # Test 2: Login with JSON
    print("\n[Test 2] Login with JSON...")
    response = client.post(
        "/auth/login/json",
        json={
            "identifier": "login_test@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    print("✓ JSON login successful")

    # Test 3: Login with wrong password
    print("\n[Test 3] Login with wrong password...")
    response = client.post(
        "/auth/login/json",
        json={
            "identifier": "login_test@test.com",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
    print("✓ Wrong password rejected correctly")

    # Test 4: Login with non-existent user
    print("\n[Test 4] Login with non-existent user...")
    response = client.post(
        "/auth/login/json",
        json={
            "identifier": "nonexistent@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401
    print("✓ Non-existent user rejected correctly")

    print("\n✅ Login tests passed")
    return token  # Return token for next tests


def test_authorization():
    """Test authorization (permissions)"""
    print("\n" + "=" * 60)
    print("TEST: Authorization (Teacher/Student)")
    print("=" * 60)

    # Setup: Register teacher and student
    client.post(
        "/auth/register",
        json={
            "identifier": "teacher_perm@test.com",
            "password": "password123",
            "role": "teacher",
            "username": "perm_teacher"
        }
    )

    client.post(
        "/auth/register",
        json={
            "identifier": "student_perm@test.com",
            "password": "password123",
            "role": "student",
            "username": "perm_student"
        }
    )

    # Get tokens
    teacher_response = client.post(
        "/auth/login/json",
        json={"identifier": "teacher_perm@test.com", "password": "password123"}
    )
    teacher_token = teacher_response.json()["access_token"]

    student_response = client.post(
        "/auth/login/json",
        json={"identifier": "student_perm@test.com", "password": "password123"}
    )
    student_token = student_response.json()["access_token"]

    # Test 1: Teacher accessing teacher endpoint (should work)
    print("\n[Test 1] Teacher accessing teacher endpoint...")
    response = client.get(
        "/test/teacher-only",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "teacher access granted"
    print(f"✓ Teacher access granted: {data['teacher']}")

    # Test 2: Student accessing teacher endpoint (should fail - 403)
    print("\n[Test 2] Student accessing teacher endpoint...")
    response = client.get(
        "/test/teacher-only",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403
    print("✓ Student denied access to teacher endpoint (403 Forbidden)")

    # Test 3: Student accessing student endpoint (should work)
    print("\n[Test 3] Student accessing student endpoint...")
    response = client.get(
        "/test/student-only",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "student access granted"
    print(f"✓ Student access granted: {data['student']}")

    # Test 4: Teacher accessing student endpoint (should fail - 403)
    print("\n[Test 4] Teacher accessing student endpoint...")
    response = client.get(
        "/test/student-only",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 403
    print("✓ Teacher denied access to student endpoint (403 Forbidden)")

    # Test 5: No token (should fail - 401)
    print("\n[Test 5] Accessing protected endpoint without token...")
    response = client.get("/test/teacher-only")
    assert response.status_code == 401
    print("✓ No token rejected (401 Unauthorized)")

    # Test 6: Invalid token (should fail - 401)
    print("\n[Test 6] Accessing with invalid token...")
    response = client.get(
        "/test/teacher-only",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    print("✓ Invalid token rejected (401 Unauthorized)")

    print("\n✅ Authorization tests passed")


if __name__ == "__main__":
    print("\n" + "🔐 " * 20)
    print("AUTH API TESTS")
    print("🔐 " * 20 + "\n")

    # Run tests
    test_registration()
    test_login()
    test_authorization()

    print("\n" + "🎉 " * 20)
    print("ALL AUTH API TESTS COMPLETE")
    print("🎉 " * 20 + "\n")

    print("Summary:")
    print("  ✓ /auth/register works correctly")
    print("  ✓ /auth/login (OAuth2) works correctly")
    print("  ✓ /auth/login/json works correctly")
    print("  ✓ Invalid credentials rejected")
    print("  ✓ Duplicate registration rejected")
    print("  ✓ Teacher permissions enforced (403)")
    print("  ✓ Student permissions enforced (403)")
    print("  ✓ Authentication required (401)")
    print("\n✅ Auth system fully functional at HTTP layer!")
