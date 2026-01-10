"""Spot configuration loader."""
import json
import os
from typing import List
from pathlib import Path
from core.chess_engine.spot.models import SpotConfig
from core.log.log_chess_engine import logger


def load_spots_from_env() -> List[SpotConfig]:
    """
    Load spot configurations from environment variable.

    Expects ENGINE_SPOTS environment variable with JSON array:
    [{"id": "spot1", "url": "http://...", ...}, ...]

    Returns:
        List of SpotConfig objects, or empty list if not configured
    """
    engine_spots = os.getenv("ENGINE_SPOTS", "")
    if not engine_spots:
        return []

    try:
        spots_data = json.loads(engine_spots)
        if not isinstance(spots_data, list):
            logger.error(f"ENGINE_SPOTS must be a JSON array, got: {type(spots_data)}")
            return []

        configs = []
        for spot_data in spots_data:
            try:
                config = SpotConfig(**spot_data)
                configs.append(config)
            except Exception as e:
                logger.error(f"Invalid spot config: {spot_data}, error: {e}")
                continue

        logger.info(f"Loaded {len(configs)} spots from ENGINE_SPOTS env var")
        return configs

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ENGINE_SPOTS: {e}")
        return []


def load_spots_from_file(file_path: str | Path) -> List[SpotConfig]:
    """
    Load spot configurations from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of SpotConfig objects, or empty list if file doesn't exist or invalid
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"Spots config file not found: {file_path}")
        return []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        spots_data = data.get("spots", [])
        if not isinstance(spots_data, list):
            logger.error(f"'spots' field must be an array in {file_path}")
            return []

        configs = []
        for spot_data in spots_data:
            try:
                config = SpotConfig(**spot_data)
                configs.append(config)
            except Exception as e:
                logger.error(f"Invalid spot config in {file_path}: {spot_data}, error: {e}")
                continue

        logger.info(f"Loaded {len(configs)} spots from {file_path}")
        return configs

    except Exception as e:
        logger.error(f"Error loading spots from {file_path}: {e}")
        return []


def load_spots(file_path: str | Path | None = None) -> List[SpotConfig]:
    """
    Load spot configurations from environment or file.

    Priority:
    1. Environment variable ENGINE_SPOTS
    2. File specified by file_path parameter
    3. Default file backend/spots.json (if exists)

    Args:
        file_path: Optional path to JSON config file

    Returns:
        List of SpotConfig objects
    """
    # Try environment variable first
    configs = load_spots_from_env()
    if configs:
        return configs

    # Try specified file
    if file_path:
        configs = load_spots_from_file(file_path)
        if configs:
            return configs

    # Try default file
    default_file = Path(__file__).parent.parent.parent.parent / "spots.json"
    configs = load_spots_from_file(default_file)
    if configs:
        return configs

    logger.warning("No spot configurations found")
    return []
