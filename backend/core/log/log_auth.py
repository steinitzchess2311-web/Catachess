"""
Authentication Logger

Logs all authentication and authorization operations including:
- User login attempts (successful and failed)
- Token generation
- Token validation
- Permission checks
- Security events
"""
from core.log import setup_logger

logger = setup_logger(
    name="auth",
    log_file="auth.log"
)
