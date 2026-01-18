"""
Workspace API app factory (test-friendly).
"""
from .app import app


def create_app():
    return app
