"""
Routers package - HTTP API endpoints
"""
from . import auth, assignments, user_profile, game_storage, chess_engine, chess_rules, imitator

__all__ = [
    "auth",
    "assignments",
    "user_profile",
    "game_storage",
    "chess_engine",
    "chess_rules",
    "imitator",
]
