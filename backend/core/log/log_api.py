"""
API Logger

Logs all API operations including:
- HTTP requests
- Request parameters
- Response status codes
- API errors
- Performance metrics
"""
from core.log import setup_logger

logger = setup_logger(
    name="api",
    log_file="api.log"
)
