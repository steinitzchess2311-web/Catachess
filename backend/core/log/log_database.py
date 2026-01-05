"""
Database Logger

Logs all database operations including:
- Connection establishment
- Query execution
- Transaction commits/rollbacks
- Migration operations
- Database errors
"""
from core.log import setup_logger

logger = setup_logger(
    name="database",
    log_file="database.log"
)
