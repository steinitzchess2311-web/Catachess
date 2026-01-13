#!/usr/bin/env python3
"""
Standalone script to run PGN tag analysis.

Usage:
    python run_analysis.py data/pgn/sample.pgn
    python run_analysis.py data/pgn/sample.pgn --max-positions 10
"""

import sys
import os

# Add parent directory to path so we can import the tagger modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.core.tagger.analysis.cli import main

if __name__ == "__main__":
    main()
