"""
Created at: 2026-07-08 23:25 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Last Modified by: Codex

Routers package - HTTP API endpoints
"""
from . import auth, assignments, user_profile, game_storage, chess_engine, chess_rules, imitator, predictor
from .tagger import router as tagger_router

__all__ = [
    "auth",
    "assignments",
    "user_profile",
    "game_storage",
    "chess_engine",
    "chess_rules",
    "imitator",
    "predictor",
    "tagger_router",
]
