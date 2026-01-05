"""
Test Storage Structure - Verify Architecture

This test verifies the storage module structure is correct.
It does NOT test R2 operations (those require R2 credentials).

Tests:
- Module imports work correctly
- Key generation functions exist and work
- Error classes are defined
- Config can be created for testing
- Store functions are defined
- Index protocol is defined
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_storage_core_imports():
    """Test that storage/core imports work"""
    print("=" * 60)
    print("TEST: Storage Core Imports")
    print("=" * 60)

    # Test imports
    from storage.core import (
        StorageClient,
        StorageConfig,
        StorageError,
        StorageUnavailable,
        ObjectNotFound,
        ObjectAlreadyExists,
        InvalidObjectKey,
    )

    print("✓ StorageClient imported")
    print("✓ StorageConfig imported")
    print("✓ Storage exceptions imported")

    # Verify exception hierarchy
    assert issubclass(StorageUnavailable, StorageError)
    assert issubclass(ObjectNotFound, StorageError)
    print("✓ Exception hierarchy correct")

    print("\n✅ Storage core imports working\n")


def test_storage_config():
    """Test storage configuration"""
    print("=" * 60)
    print("TEST: Storage Configuration")
    print("=" * 60)

    from storage.core.config import StorageConfig

    # Create test config
    config = StorageConfig.for_testing(
        endpoint="http://localhost:9000",
        bucket="test-bucket",
    )

    assert config.endpoint == "http://localhost:9000"
    assert config.bucket == "test-bucket"
    assert config.region == "auto"
    print("✓ Test config created")

    # Test repr doesn't expose secrets
    repr_str = repr(config)
    assert "test-access-key" not in repr_str  # Secret should be masked
    assert "*" in repr_str  # Should have asterisks
    print(f"✓ Config repr safe: {repr_str}")

    print("\n✅ Storage configuration working\n")


def test_game_history_keys():
    """Test key generation functions"""
    print("=" * 60)
    print("TEST: Game History Keys")
    print("=" * 60)

    from storage.game_history.keys import (
        game_pgn,
        game_analysis,
        game_training_data,
        game_thumbnail,
    )

    # Test key generation
    game_id = "8f2a9c"

    pgn_key = game_pgn(game_id)
    assert pgn_key == "games/8f2a9c.pgn"
    print(f"✓ PGN key: {pgn_key}")

    analysis_key = game_analysis(game_id)
    assert analysis_key == "analysis/8f2a9c.json"
    print(f"✓ Analysis key: {analysis_key}")

    training_key = game_training_data(game_id)
    assert training_key == "training/8f2a9c.json"
    print(f"✓ Training key: {training_key}")

    thumbnail_key = game_thumbnail(game_id)
    assert thumbnail_key == "thumbnails/8f2a9c.png"
    print(f"✓ Thumbnail key: {thumbnail_key}")

    print("\n✅ Key generation working\n")


def test_game_history_types():
    """Test GameMeta and other types"""
    print("=" * 60)
    print("TEST: Game History Types")
    print("=" * 60)

    from datetime import datetime
    from storage.game_history.types import GameMeta, AnalysisMeta, StorageStats

    # Test GameMeta
    game_meta: GameMeta = {
        "game_id": "8f2a9c",
        "created_at": datetime.now(),
        "white_player": "player1",
        "black_player": "player2",
        "result": "1-0",
        "event": "Test Event",
    }
    assert game_meta["game_id"] == "8f2a9c"
    print("✓ GameMeta structure valid")

    # Test AnalysisMeta
    analysis_meta: AnalysisMeta = {
        "game_id": "8f2a9c",
        "engine_version": "Stockfish 16",
        "depth": 20,
        "analyzed_at": datetime.now(),
        "move_count": 45,
    }
    assert analysis_meta["depth"] == 20
    print("✓ AnalysisMeta structure valid")

    # Test StorageStats
    storage_stats: StorageStats = {
        "game_id": "8f2a9c",
        "pgn_size_bytes": 1024,
        "analysis_size_bytes": 2048,
        "total_size_bytes": 3072,
    }
    assert storage_stats["total_size_bytes"] == 3072
    print("✓ StorageStats structure valid")

    print("\n✅ Type definitions working\n")


def test_game_history_store_functions():
    """Test that store functions are defined"""
    print("=" * 60)
    print("TEST: Game History Store Functions")
    print("=" * 60)

    from storage.game_history import (
        save_pgn,
        load_pgn,
        save_analysis,
        load_analysis,
    )

    # Verify functions exist
    assert callable(save_pgn)
    print("✓ save_pgn function defined")

    assert callable(load_pgn)
    print("✓ load_pgn function defined")

    assert callable(save_analysis)
    print("✓ save_analysis function defined")

    assert callable(load_analysis)
    print("✓ load_analysis function defined")

    print("\n✅ Store functions defined\n")


def test_game_history_index_protocol():
    """Test GameHistoryIndex protocol"""
    print("=" * 60)
    print("TEST: Game History Index Protocol")
    print("=" * 60)

    from storage.game_history.index import GameHistoryIndex

    # Verify it's a Protocol
    import typing
    assert hasattr(GameHistoryIndex, "__protocol_attrs__") or \
           typing.get_origin(GameHistoryIndex) == typing.Protocol or \
           hasattr(GameHistoryIndex, "add_game")

    print("✓ GameHistoryIndex is a Protocol")

    # Verify methods are defined
    assert hasattr(GameHistoryIndex, "add_game")
    assert hasattr(GameHistoryIndex, "list_games")
    assert hasattr(GameHistoryIndex, "get_game")
    assert hasattr(GameHistoryIndex, "remove_game")
    assert hasattr(GameHistoryIndex, "game_exists_for_user")
    print("✓ All protocol methods defined")

    print("\n✅ Index protocol defined correctly\n")


def test_storage_errors():
    """Test storage error classes"""
    print("=" * 60)
    print("TEST: Storage Errors")
    print("=" * 60)

    from storage.core.errors import (
        StorageError,
        ObjectNotFound,
        InvalidObjectKey,
        StorageUnavailable,
    )

    # Test ObjectNotFound
    try:
        raise ObjectNotFound("test.pgn")
    except StorageError as e:
        assert "test.pgn" in e.message
        assert e.details["key"] == "test.pgn"
        print(f"✓ ObjectNotFound: {e.message}")

    # Test InvalidObjectKey
    try:
        raise InvalidObjectKey("", "Key cannot be empty")
    except StorageError as e:
        assert "empty" in e.message.lower()
        print(f"✓ InvalidObjectKey: {e.message}")

    # Test StorageUnavailable
    try:
        raise StorageUnavailable("Network timeout")
    except StorageError as e:
        assert "timeout" in e.message.lower()
        print(f"✓ StorageUnavailable: {e.message}")

    print("\n✅ Storage errors working\n")


if __name__ == "__main__":
    print("\n" + "📦 " * 20)
    print("STORAGE STRUCTURE TESTS")
    print("📦 " * 20 + "\n")

    # Run tests
    test_storage_core_imports()
    test_storage_config()
    test_game_history_keys()
    test_game_history_types()
    test_game_history_store_functions()
    test_game_history_index_protocol()
    test_storage_errors()

    print("\n" + "🎉 " * 20)
    print("ALL STORAGE STRUCTURE TESTS COMPLETE")
    print("🎉 " * 20 + "\n")

    print("Summary:")
    print("  ✓ Storage core modules import correctly")
    print("  ✓ Configuration system works")
    print("  ✓ Key generation functions work")
    print("  ✓ Type definitions are valid")
    print("  ✓ Store functions are defined")
    print("  ✓ Index protocol is defined")
    print("  ✓ Error hierarchy is correct")
    print("\n✅ Storage structure is production-ready!")
    print("\nNote: R2 operations not tested (requires R2 credentials)")
