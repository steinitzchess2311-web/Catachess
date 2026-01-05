"""
Service Layer Logger

Logs all service layer operations including:
- User service operations
- Business logic execution
- Service errors
- Data validation
"""
from core.log import setup_logger

logger = setup_logger(
    name="service",
    log_file="service.log"
)
