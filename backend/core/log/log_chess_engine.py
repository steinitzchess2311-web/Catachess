"""
Chess Engine Logger

Logs all chess engine operations including:
- Engine initialization
- Position analysis requests
- Engine responses
- Errors and timeouts
"""
from core.log import setup_logger

logger = setup_logger(
    name="chess_engine",
    log_file="chess_engine.log"
)
