# Chess Engine Module

> Multi-spot Stockfish engine orchestration with automatic failover

This module provides a resilient chess engine client that can route requests across multiple Stockfish engine spots, with automatic failover, priority-based selection, and comprehensive metrics tracking.

## Table of Contents

- [Features](#features)
- [File Structure](#file-structure)
- [Pipeline & Architecture](#pipeline--architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)

---

## Features

- ✅ **Automatic Failover** - Seamlessly switches to backup spots on timeout or error
- ✅ **Priority-Based Routing** - Intelligent spot selection (priority → latency → success rate)
- ✅ **Fast Timeout** - 30-second timeout (vs 60s legacy) for faster failure detection
- ✅ **Configurable Retry** - Configurable max retries (default: 2 retries = 3 total attempts)
- ✅ **Real-Time Metrics** - Track latency, success rate, and failures per spot
- ✅ **Backward Compatible** - Feature flag with graceful fallback to single-spot mode
- ✅ **Comprehensive Logging** - Detailed routing decisions and error reporting

---

## File Structure

```
backend/core/chess_engine/
├── __init__.py                     # Public API & factory function
├── client.py                       # Legacy single-spot client
├── schemas.py                      # Data models (EngineResult, EngineLine)
├── exceptions.py                   # Custom exceptions
│
├── orchestrator/                   # Multi-spot orchestration layer
│   ├── __init__.py
│   ├── orchestrator.py             # Main request router with failover logic
│   ├── pool.py                     # Spot pool management & lifecycle
│   └── selector.py                 # Spot selection algorithm
│
├── spot/                           # Individual spot management
│   ├── __init__.py
│   ├── spot.py                     # Single spot client wrapper
│   └── models.py                   # Spot data models (config, metrics, status)
│
└── config/                         # Configuration loading
    ├── __init__.py
    └── spots.py                    # Spot configuration loader
```

### File Descriptions

#### Core Files

**`__init__.py`** (51 lines)
- Exports public API: `get_engine()`, `EngineClient`, `EngineOrchestrator`
- **`get_engine()`** - Factory function that returns appropriate engine based on `ENABLE_MULTI_SPOT` flag
- Loads spot configurations from environment or file
- Handles graceful fallback to legacy mode

**`client.py`** (103 lines) - **[LEGACY]**
- Original single-spot engine client
- Direct HTTP calls to single Stockfish engine
- Maintained for backward compatibility

**`schemas.py`** (20 lines)
- `EngineResult` - Analysis result container
- `EngineLine` - Single PV line (multipv, score, pv)
- Pydantic models for type safety

**`exceptions.py`**
- `EngineError` - Base engine exception
- `EngineTimeoutError` - Timeout-specific exception

#### Orchestrator Layer

**`orchestrator/orchestrator.py`** (87 lines)
- **`EngineOrchestrator`** - Main request router
- Coordinates failover across multiple spots
- Implements retry logic with configurable max_retries
- Aggregates errors and logs routing decisions
- **Public API:** `analyze(fen, depth, multipv)` - matches legacy EngineClient API

**`orchestrator/pool.py`** (101 lines)
- **`EngineSpotPool`** - Manages pool of engine spots
- Spot registration and lifecycle management
- Enable/disable spot functionality
- Integrates with selector for spot selection
- **Key Methods:**
  - `register_spot(config)` - Add spot to pool
  - `get_best_spot()` - Get optimal spot for request
  - `get_usable_spots()` - Get all usable spots in priority order
  - `enable_spot(id)` / `disable_spot(id)` - Manual spot control

**`orchestrator/selector.py`** (71 lines)
- **`SpotSelector`** - Spot selection algorithm
- **Selection Priority:**
  1. Health status: HEALTHY > DEGRADED > DOWN
  2. Priority (higher first)
  3. Average latency (lower first)
  4. Success rate (higher first)
- **Key Methods:**
  - `select_best(spots)` - Returns single best spot
  - `select_all_usable(spots)` - Returns all usable spots in priority order

#### Spot Layer

**`spot/spot.py`** (132 lines)
- **`EngineSpot`** - Individual spot client
- Wraps HTTP calls to single engine spot
- Automatically tracks metrics on success/failure
- Implements health check endpoint support
- **Key Methods:**
  - `analyze(fen, depth, multipv)` - Analyze position (same API as EngineClient)
  - `health_check()` - Check if spot is healthy
  - `metrics` - Access spot metrics (latency, success rate, etc.)

**`spot/models.py`** (54 lines)
- **`SpotStatus`** - Enum: HEALTHY, DEGRADED, DOWN, UNKNOWN
- **`SpotConfig`** - Spot configuration (id, url, region, priority, enabled)
- **`SpotMetrics`** - Runtime metrics with automatic calculations
  - `avg_latency_ms` - Rolling average latency
  - `success_rate` - Success rate (0.0 to 1.0)
  - `last_healthy_at` - Last successful request timestamp
  - `failure_count` - Total failures
  - `total_requests` - Total requests
  - `update_success(latency_ms)` - Record successful request
  - `update_failure()` - Record failed request

#### Configuration

**`config/spots.py`** (98 lines)
- Loads spot configurations from multiple sources
- **Loading Priority:**
  1. Environment variable `ENGINE_SPOTS` (JSON array)
  2. Specified file path
  3. Default file `backend/spots.json`
- **Key Functions:**
  - `load_spots()` - Load from all sources with fallback
  - `load_spots_from_env()` - Load from ENGINE_SPOTS env var
  - `load_spots_from_file(path)` - Load from JSON file

---

## Pipeline & Architecture

### Request Flow (Multi-Spot Mode)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. User Request                                                │
│     POST /analyze {fen, depth, multipv}                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. FastAPI Endpoint (app.py)                                   │
│     - Receives request                                          │
│     - Calls engine.analyze()                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. get_engine() Factory (__init__.py)                          │
│     - Checks ENABLE_MULTI_SPOT flag                             │
│     - Returns EngineOrchestrator (multi) or EngineClient (single)│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. EngineOrchestrator (orchestrator.py)                        │
│     - analyze() called                                          │
│     - Gets usable spots from pool                               │
│     - Max attempts = min(usable_spots, max_retries + 1)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. EngineSpotPool (pool.py)                                    │
│     - get_usable_spots() called                                 │
│     - Gets all spots with metrics                               │
│     - Passes to selector                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. SpotSelector (selector.py)                                  │
│     - Filters: enabled && (HEALTHY || DEGRADED)                 │
│     - Sorts by: priority DESC, latency ASC, success_rate DESC   │
│     - Returns prioritized list                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Try Spot #1 (spot.py)                                       │
│     - EngineSpot.analyze() called                               │
│     - HTTP GET to spot1_url/analyze/stream                      │
│     - Timeout: 30 seconds                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
           ┌──────────────┐    ┌──────────────┐
           │  Success     │    │  Failure     │
           │              │    │  (timeout/   │
           │              │    │   error)     │
           └──────┬───────┘    └──────┬───────┘
                  │                   │
                  │                   ▼
                  │            ┌─────────────────────────┐
                  │            │  8. Failover            │
                  │            │     Try Spot #2         │
                  │            │     (same process)      │
                  │            └──────┬──────────────────┘
                  │                   │
                  │         ┌─────────┴─────────┐
                  │         │                   │
                  │         ▼                   ▼
                  │    ┌─────────┐       ┌──────────┐
                  │    │ Success │       │  Failure │
                  │    └────┬────┘       └────┬─────┘
                  │         │                 │
                  │         │                 ▼
                  │         │          ┌─────────────┐
                  │         │          │  Try Spot #3│
                  │         │          └──────┬──────┘
                  │         │                 │
                  └─────────┴─────────────────┴───────────┐
                                                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. Update Metrics (spot.py)                                    │
│     - On success: update_success(latency_ms)                    │
│     - On failure: update_failure()                              │
│     - Updates: total_requests, failure_count, avg_latency,      │
│                success_rate, last_healthy_at                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  10. Return Result                                              │
│      - EngineResult(lines=[...]) on success                     │
│      - ChessEngineError on all spots failed                     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Relationships

```
                    ┌──────────────────┐
                    │   get_engine()   │
                    └────────┬─────────┘
                             │
             ┌───────────────┴────────────────┐
             │                                │
             ▼                                ▼
    ┌─────────────────┐            ┌──────────────────┐
    │  EngineClient   │            │EngineOrchestrator│
    │   (Legacy)      │            │   (Multi-spot)   │
    └─────────────────┘            └────────┬─────────┘
                                            │ owns
                                            ▼
                                   ┌──────────────────┐
                                   │ EngineSpotPool   │
                                   └────────┬─────────┘
                                            │ owns
                              ┌─────────────┼─────────────┐
                              │             │             │
                              ▼             ▼             ▼
                        ┌─────────┐   ┌─────────┐   ┌─────────┐
                        │ Spot #1 │   │ Spot #2 │   │ Spot #N │
                        └─────────┘   └─────────┘   └─────────┘
                              │             │             │
                              └─────────────┼─────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │  SpotSelector   │
                                  │  (Algorithm)    │
                                  └─────────────────┘
```

### State Transitions

**Spot Status State Machine:**
```
┌─────────┐
│ UNKNOWN │ ← Initial state
└────┬────┘
     │ first health check
     │
     ├─ success ───→ ┌─────────┐
     │               │ HEALTHY │ ← Working normally
     │               └────┬────┘
     │                    │
     │                    │ 1-2 failures
     │                    ▼
     │               ┌──────────┐
     └─ failure ───→ │DEGRADED  │ ← Partial failures
                     └────┬─────┘
                          │
                          │ 3+ consecutive failures
                          ▼
                     ┌─────────┐
                     │  DOWN   │ ← Unavailable
                     └────┬────┘
                          │
                          │ health check success
                          └──────────────────────┐
                                                 ▼
                                          Back to HEALTHY
```

### Failover Decision Tree

```
Request arrives
    │
    ├─ Get usable spots
    │   │
    │   ├─ Filter: enabled == true
    │   ├─ Filter: status in (HEALTHY, DEGRADED)
    │   ├─ Sort by: priority DESC → latency ASC → success_rate DESC
    │   └─ Return prioritized list
    │
    ├─ No usable spots?
    │   └─ Raise ChessEngineError("No spots available")
    │
    ├─ Try Spot #1
    │   ├─ Success? → Return result
    │   └─ Failure? → Continue
    │
    ├─ Retry count < max_retries?
    │   ├─ Yes: Try Spot #2
    │   │   ├─ Success? → Return result
    │   │   └─ Failure? → Continue
    │   │
    │   └─ No: Raise ChessEngineError("All spots failed")
    │
    └─ Return result or error
```

---

## Usage

### Basic Usage (Automatic Mode Selection)

```python
from core.chess_engine import get_engine

# Automatically selects single-spot or multi-spot based on config
engine = get_engine()

# Analyze a position
result = engine.analyze(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    depth=15,
    multipv=3
)

# Access results
for line in result.lines:
    print(f"PV{line.multipv}: score={line.score}, moves={' '.join(line.pv)}")
```

### Direct Multi-Spot Usage

```python
from core.chess_engine.orchestrator.orchestrator import EngineOrchestrator
from core.chess_engine.spot.models import SpotConfig

# Define spots
spots = [
    SpotConfig(id="spot1", url="http://192.168.40.33:8001", priority=100),
    SpotConfig(id="spot2", url="http://192.168.40.41:5000", priority=90),
]

# Create orchestrator
orchestrator = EngineOrchestrator(
    spot_configs=spots,
    timeout=30,
    max_retries=2
)

# Analyze
result = orchestrator.analyze(fen="...", depth=15, multipv=3)
```

### Accessing Metrics

```python
engine = get_engine()

# Get metrics for all spots
metrics = engine.get_spot_metrics()
for config, metrics in metrics:
    print(f"{config.id}: {metrics.status}")
    print(f"  Latency: {metrics.avg_latency_ms:.1f}ms")
    print(f"  Success rate: {metrics.success_rate:.2%}")
    print(f"  Total requests: {metrics.total_requests}")
```

### Manual Spot Control

```python
engine = get_engine()

# Disable a spot
engine.disable_spot("spot1")

# Enable a spot
engine.enable_spot("spot1")
```

---

## Configuration

### Option 1: Environment Variables

```bash
# Enable multi-spot mode
export ENABLE_MULTI_SPOT=true

# Define spots as JSON array
export ENGINE_SPOTS='[
  {
    "id": "cn-shanghai",
    "url": "http://192.168.40.33:8001",
    "region": "cn-east",
    "priority": 100,
    "enabled": true
  },
  {
    "id": "cn-local",
    "url": "http://192.168.40.41:5000",
    "region": "cn-local",
    "priority": 90,
    "enabled": true
  }
]'

# Configure timeouts and retries
export SPOT_REQUEST_TIMEOUT=30
export SPOT_MAX_RETRIES=2
```

### Option 2: JSON File

Create `backend/spots.json`:

```json
{
  "spots": [
    {
      "id": "cn-shanghai",
      "url": "http://192.168.40.33:8001",
      "region": "cn-east",
      "priority": 100,
      "enabled": true
    },
    {
      "id": "cn-local",
      "url": "http://192.168.40.41:5000",
      "region": "cn-local",
      "priority": 90,
      "enabled": true
    }
  ]
}
```

Then enable in `.env`:
```bash
ENABLE_MULTI_SPOT=true
SPOT_REQUEST_TIMEOUT=30
SPOT_MAX_RETRIES=2
```

### Configuration Fields

**SpotConfig:**
- `id` (required) - Unique identifier for the spot
- `url` (required) - HTTP endpoint (e.g., "http://192.168.40.33:8001")
- `region` (optional) - Geographic region (default: "unknown")
- `priority` (optional) - Selection priority 0-200 (default: 100, higher = preferred)
- `enabled` (optional) - Manual enable/disable (default: true)

**Settings:**
- `ENABLE_MULTI_SPOT` - Feature flag (default: false)
- `ENGINE_SPOTS` - JSON array of spot configs
- `SPOT_REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)
- `SPOT_MAX_RETRIES` - Max retry attempts (default: 2, total attempts = max_retries + 1)

### Legacy Single-Spot Mode

Keep multi-spot disabled (default):
```bash
ENABLE_MULTI_SPOT=false
ENGINE_URL=http://192.168.40.33:8001
ENGINE_TIMEOUT=60
```

---

## API Reference

### Public API

#### `get_engine() -> EngineClient | EngineOrchestrator`

Factory function that returns appropriate engine implementation.

**Returns:**
- `EngineOrchestrator` if `ENABLE_MULTI_SPOT=true` and spots configured
- `EngineClient` otherwise (legacy mode)

**Example:**
```python
from core.chess_engine import get_engine
engine = get_engine()
```

---

### EngineOrchestrator

Main multi-spot engine client.

#### `__init__(spot_configs, timeout=30, max_retries=2)`

**Parameters:**
- `spot_configs` (List[SpotConfig]) - List of spot configurations
- `timeout` (int) - Request timeout in seconds (default: 30)
- `max_retries` (int) - Maximum retry attempts (default: 2)

#### `analyze(fen, depth=15, multipv=3) -> EngineResult`

Analyze a chess position with automatic failover.

**Parameters:**
- `fen` (str) - FEN string
- `depth` (int) - Analysis depth (default: 15)
- `multipv` (int) - Number of principal variations (default: 3)

**Returns:**
- `EngineResult` - Analysis result with lines

**Raises:**
- `ChessEngineError` - If all spots fail or no spots available
- `ChessEngineTimeoutError` - If request times out

**Example:**
```python
result = orchestrator.analyze(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    depth=20,
    multipv=5
)
```

#### `get_spot_metrics() -> List[Tuple[SpotConfig, SpotMetrics]]`

Get metrics for all spots.

**Returns:**
- List of (config, metrics) tuples

#### `enable_spot(spot_id: str) -> bool`

Enable a spot.

**Parameters:**
- `spot_id` (str) - Spot identifier

**Returns:**
- `bool` - True if successful, False if spot not found

#### `disable_spot(spot_id: str) -> bool`

Disable a spot.

**Parameters:**
- `spot_id` (str) - Spot identifier

**Returns:**
- `bool` - True if successful, False if spot not found

---

### Data Models

#### `EngineResult`

Analysis result container.

**Fields:**
- `lines` (List[EngineLine]) - List of analysis lines

#### `EngineLine`

Single principal variation.

**Fields:**
- `multipv` (int) - PV number (1, 2, 3, ...)
- `score` (int | str) - Centipawn score or "mateN"
- `pv` (List[str]) - Principal variation moves (UCI format)

#### `SpotConfig`

Spot configuration.

**Fields:**
- `id` (str) - Unique identifier
- `url` (str) - HTTP endpoint
- `region` (str) - Geographic region
- `priority` (int) - Selection priority (0-200)
- `enabled` (bool) - Manual enable/disable

#### `SpotMetrics`

Runtime metrics for a spot.

**Fields:**
- `status` (SpotStatus) - Current health status
- `avg_latency_ms` (float) - Rolling average latency
- `success_rate` (float) - Success rate (0.0 to 1.0)
- `last_healthy_at` (datetime | None) - Last successful request
- `failure_count` (int) - Total failures
- `total_requests` (int) - Total requests

**Methods:**
- `update_success(latency_ms: float)` - Record successful request
- `update_failure()` - Record failed request

#### `SpotStatus`

Health status enum.

**Values:**
- `HEALTHY` - Working normally
- `DEGRADED` - Partial failures
- `DOWN` - Unavailable
- `UNKNOWN` - Not yet checked

---

## Testing

### Test Structure

```
tests/
├── chess_engine/
│   ├── spot/
│   │   ├── test_models.py          # 14 tests - Data models
│   │   └── test_spot.py            # 15 tests - Spot client
│   └── orchestrator/
│       ├── test_selector.py        # 20 tests - Selection algorithm
│       ├── test_pool.py            # 17 tests - Pool management
│       └── test_orchestrator.py    # 15 tests - Orchestrator logic
└── integration/
    └── test_multi_spot_integration.py  # 10 tests - End-to-end
```

### Running Tests

Each test file has a built-in runner:

```bash
cd /home/catadragon/Code/catachess

# Run individual test files
python3 tests/chess_engine/spot/test_models.py
python3 tests/chess_engine/spot/test_spot.py
python3 tests/chess_engine/orchestrator/test_selector.py
python3 tests/chess_engine/orchestrator/test_pool.py
python3 tests/chess_engine/orchestrator/test_orchestrator.py
python3 tests/integration/test_multi_spot_integration.py
```

### Test Coverage

**Unit Tests (81 tests):**
- ✅ Data models and validation
- ✅ Spot client (success, timeout, errors)
- ✅ Selection algorithm (priority, latency, success rate)
- ✅ Pool management (registration, enable/disable)
- ✅ Orchestrator (routing, failover, retry logic)

**Integration Tests (10 tests):**
- ✅ End-to-end successful analysis
- ✅ Failover scenarios
- ✅ Priority ordering
- ✅ Metrics accumulation
- ✅ Edge cases (all spots down, disabled spots)

**Total:** 91 tests covering all critical paths

---

## Troubleshooting

### No Spots Available Error

**Symptom:** `ChessEngineError: No engine spots available`

**Causes:**
- Multi-spot enabled but no spots configured
- All spots disabled or marked as DOWN
- Invalid spot configuration

**Solutions:**
1. Check `ENGINE_SPOTS` environment variable or `backend/spots.json`
2. Verify at least one spot is enabled
3. Check spot health status in logs

### Timeout Issues

**Symptom:** Frequent timeouts, slow failover

**Causes:**
- Spot URLs are incorrect or unreachable
- Network latency too high
- Timeout too short for analysis depth

**Solutions:**
1. Verify spot URLs are accessible: `curl http://spot-url/health`
2. Increase timeout: `SPOT_REQUEST_TIMEOUT=60`
3. Check network connectivity
4. Reduce analysis depth for faster results

### All Spots Failing

**Symptom:** All requests fail after trying all spots

**Causes:**
- All engine spots are down
- Network issues
- Authentication issues

**Solutions:**
1. Check engine spot status manually
2. Review logs for error details
3. Test spots individually with curl
4. Verify firewall rules allow connections

### Metrics Not Updating

**Symptom:** Metrics show 0 requests or incorrect values

**Causes:**
- Spots not being used (all disabled or DOWN)
- Legacy mode active (multi-spot disabled)

**Solutions:**
1. Verify `ENABLE_MULTI_SPOT=true`
2. Check spot status: `engine.get_spot_metrics()`
3. Review logs for routing decisions

---

## Performance

### Benchmarks

- **Routing Overhead:** < 1ms (selector algorithm)
- **Failover Time:** ~30-31s (timeout + retry overhead)
- **Memory per Spot:** ~2KB (config + metrics)
- **Supported Spots:** Unlimited (tested with 3, designed for 10+)

### Optimization Tips

1. **Set Appropriate Timeout:**
   - 30s for fast engines
   - 60s for slower engines or complex positions

2. **Tune Priority Values:**
   - Higher priority (150-200) for faster/more reliable spots
   - Lower priority (50-100) for backup spots

3. **Monitor Metrics:**
   - Regularly check success rates
   - Adjust priorities based on performance
   - Disable consistently failing spots

4. **Use Appropriate Depth:**
   - Lower depth (10-15) for faster responses
   - Higher depth (20+) for deep analysis

---

## Logging

All operations are logged to `backend/logs/chess_engine.log`:

```
INFO: EngineOrchestrator initialized: 2 spots, timeout=30s, max_retries=2
INFO: [Attempt 1/3] Routing to spot: cn-shanghai
INFO: [cn-shanghai] Analysis succeeded (124.5ms, 3 lines)
WARN: Spot cn-shanghai timed out after 30s (attempt 1/3)
INFO: [Attempt 2/3] Routing to spot: cn-local
ERROR: All spots failed after 3 attempts: spot1: timeout; spot2: timeout; spot3: connection refused
```

---

## License

Part of CataChess project.

## Support

For issues or questions, see the main project repository.
