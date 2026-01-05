"""
Application Error Classes

Custom exceptions for expected error conditions (not bugs).
These represent normal business logic failures that should be handled gracefully.

Usage:
    - Raise these exceptions in service/business logic layers
    - Catch and convert to HTTP responses in API routes
    - Log appropriately (warning for client errors, error for server issues)
"""


# ============================================================================
# Base Application Errors
# ============================================================================

class AppError(Exception):
    """
    Base exception for all application errors.
    All custom exceptions should inherit from this.
    """
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found (maps to 404)"""
    pass


class ValidationError(AppError):
    """Invalid input data (maps to 400)"""
    pass


class ConflictError(AppError):
    """Resource conflict, e.g., duplicate entry (maps to 409)"""
    pass


class UnauthorizedError(AppError):
    """Authentication failed (maps to 401)"""
    pass


class ForbiddenError(AppError):
    """Permission denied (maps to 403)"""
    pass


class ExternalServiceError(AppError):
    """External service unavailable (maps to 503)"""
    pass


# ============================================================================
# User & Authentication Errors
# ============================================================================

class UserNotFoundError(NotFoundError):
    """User does not exist"""
    def __init__(self, identifier: str):
        super().__init__(
            message=f"User not found: {identifier}",
            details={"identifier": identifier}
        )


class UserAlreadyExistsError(ConflictError):
    """User with identifier already exists"""
    def __init__(self, identifier: str):
        super().__init__(
            message=f"User already exists: {identifier}",
            details={"identifier": identifier}
        )


class InvalidCredentialsError(UnauthorizedError):
    """Invalid username/password"""
    def __init__(self):
        super().__init__(message="Invalid credentials")


class UserInactiveError(ForbiddenError):
    """User account is disabled"""
    def __init__(self, identifier: str):
        super().__init__(
            message=f"User account is inactive: {identifier}",
            details={"identifier": identifier}
        )


class InvalidTokenError(UnauthorizedError):
    """JWT token is invalid or expired"""
    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(message=reason)


class TokenExpiredError(UnauthorizedError):
    """JWT token has expired"""
    def __init__(self):
        super().__init__(message="Token has expired")


# ============================================================================
# Permission Errors
# ============================================================================

class InsufficientPermissionsError(ForbiddenError):
    """User lacks required permissions"""
    def __init__(self, required_role: str, user_role: str):
        super().__init__(
            message=f"Insufficient permissions: requires {required_role}, user has {user_role}",
            details={"required_role": required_role, "user_role": user_role}
        )


class TeacherAccessRequiredError(ForbiddenError):
    """Endpoint requires teacher role"""
    def __init__(self):
        super().__init__(message="Teacher access required")


class StudentAccessRequiredError(ForbiddenError):
    """Endpoint requires student role"""
    def __init__(self):
        super().__init__(message="Student access required")


# ============================================================================
# Chess Engine Errors
# ============================================================================

class ChessEngineError(ExternalServiceError):
    """Chess engine service error"""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=f"Chess engine error: {message}",
            details=details
        )


class ChessEngineTimeoutError(ChessEngineError):
    """Chess engine request timeout"""
    def __init__(self, timeout: int):
        super().__init__(
            message=f"Chess engine timeout after {timeout}s",
            details={"timeout": timeout}
        )


class InvalidFENError(ValidationError):
    """Invalid FEN string"""
    def __init__(self, fen: str):
        super().__init__(
            message=f"Invalid FEN notation: {fen}",
            details={"fen": fen}
        )


# ============================================================================
# Database Errors
# ============================================================================

class DatabaseError(AppError):
    """Database operation error"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Cannot connect to database"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Database connection failed: {reason}",
            details={"reason": reason}
        )


class DatabaseIntegrityError(ConflictError):
    """Database constraint violation"""
    def __init__(self, constraint: str):
        super().__init__(
            message=f"Database integrity error: {constraint}",
            details={"constraint": constraint}
        )


# ============================================================================
# Validation Errors
# ============================================================================

class InvalidEmailError(ValidationError):
    """Invalid email format"""
    def __init__(self, email: str):
        super().__init__(
            message=f"Invalid email format: {email}",
            details={"email": email}
        )


class InvalidPhoneError(ValidationError):
    """Invalid phone number format"""
    def __init__(self, phone: str):
        super().__init__(
            message=f"Invalid phone number: {phone}",
            details={"phone": phone}
        )


class WeakPasswordError(ValidationError):
    """Password does not meet requirements"""
    def __init__(self, requirements: list[str]):
        super().__init__(
            message="Password does not meet security requirements",
            details={"requirements": requirements}
        )


class InvalidRoleError(ValidationError):
    """Invalid user role"""
    def __init__(self, role: str, valid_roles: list[str]):
        super().__init__(
            message=f"Invalid role: {role}",
            details={"role": role, "valid_roles": valid_roles}
        )


# ============================================================================
# Business Logic Errors (Future)
# ============================================================================

class AssignmentNotFoundError(NotFoundError):
    """Assignment does not exist"""
    def __init__(self, assignment_id: str):
        super().__init__(
            message=f"Assignment not found: {assignment_id}",
            details={"assignment_id": assignment_id}
        )


class CourseNotFoundError(NotFoundError):
    """Course does not exist"""
    def __init__(self, course_id: str):
        super().__init__(
            message=f"Course not found: {course_id}",
            details={"course_id": course_id}
        )


class NotCourseOwnerError(ForbiddenError):
    """User is not the course owner"""
    def __init__(self, course_id: str):
        super().__init__(
            message=f"Not authorized to modify course: {course_id}",
            details={"course_id": course_id}
        )


class NotEnrolledError(ForbiddenError):
    """Student not enrolled in course"""
    def __init__(self, course_id: str):
        super().__init__(
            message=f"Not enrolled in course: {course_id}",
            details={"course_id": course_id}
        )


# ============================================================================
# Error Helper Functions
# ============================================================================

def get_error_response(error: AppError) -> dict:
    """
    Convert AppError to API response format.

    Returns:
        dict with 'error', 'message', and optional 'details'
    """
    return {
        "error": error.__class__.__name__,
        "message": error.message,
        "details": error.details if error.details else None
    }


def get_http_status_code(error: AppError) -> int:
    """
    Map AppError to HTTP status code.

    Returns:
        HTTP status code (400, 401, 403, 404, 409, 503)
    """
    if isinstance(error, NotFoundError):
        return 404
    elif isinstance(error, ValidationError):
        return 400
    elif isinstance(error, ConflictError):
        return 409
    elif isinstance(error, UnauthorizedError):
        return 401
    elif isinstance(error, ForbiddenError):
        return 403
    elif isinstance(error, ExternalServiceError):
        return 503
    else:
        return 500  # Internal server error for unknown errors
