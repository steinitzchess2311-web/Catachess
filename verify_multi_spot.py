#!/usr/bin/env python3
"""
Verification script for multi-spot engine system.
Tests that all components can be imported and initialized correctly.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("=" * 70)
print("Multi-Spot Engine System Verification")
print("=" * 70)
print()

# Test 1: Import core modules
print("✓ Test 1: Importing core modules...")
try:
    from core.chess_engine import get_engine, EngineClient, EngineOrchestrator
    print("  ✓ Imported: get_engine, EngineClient, EngineOrchestrator")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Import spot modules
print("✓ Test 2: Importing spot modules...")
try:
    from core.chess_engine.spot.models import SpotConfig, SpotMetrics, SpotStatus
    from core.chess_engine.spot.spot import EngineSpot
    print("  ✓ Imported: SpotConfig, SpotMetrics, SpotStatus, EngineSpot")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Import orchestrator modules
print("✓ Test 3: Importing orchestrator modules...")
try:
    from core.chess_engine.orchestrator.orchestrator import EngineOrchestrator
    from core.chess_engine.orchestrator.pool import EngineSpotPool
    from core.chess_engine.orchestrator.selector import SpotSelector
    print("  ✓ Imported: EngineOrchestrator, EngineSpotPool, SpotSelector")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Import config modules
print("✓ Test 4: Importing config modules...")
try:
    from core.chess_engine.config.spots import load_spots, load_spots_from_file
    print("  ✓ Imported: load_spots, load_spots_from_file")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 5: Import schemas and exceptions
print("✓ Test 5: Importing schemas and exceptions...")
try:
    from core.chess_engine.schemas import EngineResult, EngineLine
    from core.chess_engine.exceptions import EngineError
    from core.errors import ChessEngineError, ChessEngineTimeoutError
    print("  ✓ Imported: EngineResult, EngineLine, EngineError, ChessEngineError")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 6: Create SpotConfig
print("✓ Test 6: Creating SpotConfig...")
try:
    config = SpotConfig(
        id="test-spot",
        url="http://localhost:8001",
        region="test",
        priority=100
    )
    print(f"  ✓ Created SpotConfig: {config.id}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 7: Create SpotMetrics
print("✓ Test 7: Creating SpotMetrics...")
try:
    metrics = SpotMetrics(status=SpotStatus.HEALTHY)
    metrics.update_success(100.0)
    print(f"  ✓ Created SpotMetrics: status={metrics.status}, latency={metrics.avg_latency_ms}ms")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 8: Create EngineSpot
print("✓ Test 8: Creating EngineSpot...")
try:
    spot = EngineSpot(config, timeout=30)
    print(f"  ✓ Created EngineSpot: {spot.config.id}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 9: Create SpotSelector
print("✓ Test 9: Creating SpotSelector...")
try:
    selector = SpotSelector()
    # Test selection with mock data
    test_spots = [
        (SpotConfig(id="spot1", url="http://localhost:8001", priority=100),
         SpotMetrics(status=SpotStatus.HEALTHY)),
        (SpotConfig(id="spot2", url="http://localhost:8002", priority=90),
         SpotMetrics(status=SpotStatus.HEALTHY)),
    ]
    best = selector.select_best(test_spots)
    print(f"  ✓ SpotSelector selected: {best.id if best else 'None'}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 10: Create EngineSpotPool
print("✓ Test 10: Creating EngineSpotPool...")
try:
    pool = EngineSpotPool(timeout=30)
    pool.register_spot(SpotConfig(id="spot1", url="http://localhost:8001"))
    pool.register_spot(SpotConfig(id="spot2", url="http://localhost:8002"))
    print(f"  ✓ Created EngineSpotPool with {pool.get_spot_count()} spots")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 11: Create EngineOrchestrator
print("✓ Test 11: Creating EngineOrchestrator...")
try:
    spots = [
        SpotConfig(id="spot1", url="http://localhost:8001", priority=100),
        SpotConfig(id="spot2", url="http://localhost:8002", priority=90),
    ]
    orchestrator = EngineOrchestrator(spot_configs=spots, timeout=30, max_retries=2)
    print(f"  ✓ Created EngineOrchestrator with {orchestrator.pool.get_spot_count()} spots")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 12: Test get_engine() factory (legacy mode)
print("✓ Test 12: Testing get_engine() factory (legacy mode)...")
try:
    import os
    os.environ['ENABLE_MULTI_SPOT'] = 'false'

    # Reload config to pick up env change
    import importlib
    import core.config
    importlib.reload(core.config)

    engine = get_engine()
    engine_type = type(engine).__name__
    print(f"  ✓ get_engine() returned: {engine_type}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 13: Load spots from file
print("✓ Test 13: Loading spots from file...")
try:
    spots = load_spots_from_file("backend/spots.json")
    print(f"  ✓ Loaded {len(spots)} spots from backend/spots.json")
    for spot in spots:
        print(f"    - {spot.id}: {spot.url} (priority={spot.priority})")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 14: Check app.py integration
print("✓ Test 14: Checking app.py integration...")
try:
    with open("backend/app/app.py", "r") as f:
        app_content = f.read()
        if "from core.chess_engine import get_engine" in app_content:
            print("  ✓ app.py imports get_engine()")
        else:
            print("  ✗ app.py does not import get_engine()")
            sys.exit(1)

        if "engine = get_engine()" in app_content:
            print("  ✓ app.py uses get_engine()")
        else:
            print("  ✗ app.py does not use get_engine()")
            sys.exit(1)
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Summary
print()
print("=" * 70)
print("✓ All verification tests passed!")
print("=" * 70)
print()
print("Multi-spot engine system is ready to use.")
print()
print("To enable multi-spot mode:")
print("  1. Set ENABLE_MULTI_SPOT=true in .env")
print("  2. Configure spots in backend/spots.json (already created)")
print("  3. Restart the application")
print()
print("Current configuration:")
print(f"  - spots.json: {len(spots)} spots configured")
print(f"  - Feature flag: ENABLE_MULTI_SPOT={os.getenv('ENABLE_MULTI_SPOT', 'false')}")
print()
