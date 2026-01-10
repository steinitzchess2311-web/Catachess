"""
Engine interaction module for Stockfish analysis.
"""
from .stockfish_client import StockfishClient
from .protocol import EngineClient

__all__ = ["StockfishClient", "EngineClient"]
