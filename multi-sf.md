# Multi-Spot Stockfish Implementation Plan

> **Status:** READY FOR IMPLEMENTATION | **Timeline:** 15 days | **Complexity:** Medium-High

---

## Table of Contents

### Quick Start
- [📋 Quick Reference](#-quick-reference) - At-a-glance overview
- [🎯 Executive Summary](#-executive-summary) - Goals and architecture
- [Getting Started for Developers](#4-getting-started-for-developers) - **START HERE**
- [Code Templates & Examples](#5-code-templates--examples) - Copy-paste templates
- [Quick Implementation Checklist](#18-quick-implementation-checklist) - Condensed task list

### Planning & Architecture
- [Current Situation Analysis](#1-current-situation-analysis)
- [Proposed Architecture](#2-proposed-architecture)
- [Detailed File Structure](#3-detailed-file-structure)
- [Implementation Strategy](#5-implementation-strategy)

### Technical Details
- [API Changes & Integration](#6-api-changes--integration)
- [Error Handling](#7-error-handling)
- [Monitoring & Logging](#8-monitoring--logging)
- [Testing Strategy](#9-testing-strategy)
- [Performance Targets](#11-performance-targets)
- [Security Considerations](#12-security-considerations)

### Execution
- [Detailed Implementation Checklists](#13-checklists) (6 stages)
- [Deployment Considerations](#10-deployment-considerations)
- [Risk Assessment](#14-risk-assessment)
- [Success Criteria](#15-success-criteria)

### Reference
- [Future Enhancements](#16-future-enhancements)
- [Appendix](#17-appendix) - Code examples, scripts
- [File Creation Checklist](#19-file-creation-checklist)
- [Troubleshooting Guide](#20-troubleshooting-guide) - Common issues & solutions
- [Contact & Support](#21-contact--support)

---

## 📋 Quick Reference

| Aspect | Current | Target | Gain |
|--------|---------|--------|------|
| **Architecture** | Single endpoint | Multi-spot pool | Resilience |
| **Timeout** | 60s | 30s | 2x faster failure detection |
| **Availability** | ~95% (single point) | >99.5% | Failover protection |
| **Monitoring** | None | Real-time health checks | Proactive detection |
| **Spots** | 1 spot | 2+ spots (expandable) | Geographic distribution |

### Implementation Summary
```
10 new files | 600-800 LOC total | Max 100 lines/file
├── 3 orchestrator files (routing, pool, selector)
├── 3 spot files (client, health monitor, models)
├── 2 config files (loader, validation)
└── 2 integration points (__init__, app.py updates)
```

### Key Metrics
- **Routing overhead:** < 5ms (P95)
- **Failover time:** < 30s
- **Request timeout:** 30s (configurable)
- **Health check interval:** 30s

### Implementation Phases
```
Phase 1: Foundation        │██████████░░░░░░░░░░│ Days 1-3
Phase 2: Orchestration     │░░░░░░░░░░██████████│ Days 4-6
Phase 3: Integration       │░░░░░░░░░░░░░░██████│ Days 7-9
Phase 4: Testing           │░░░░░░░░░░░░░░░░████│ Days 10-12
Phase 5: Deployment        │░░░░░░░░░░░░░░░░░░██│ Days 13-15
```

### Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **Breaking changes** | Feature flag + backward compatibility layer |
| **Performance regression** | Load testing + gradual rollout (10% → 50% → 100%) |
| **All spots down** | Multiple geographies + monitoring alerts |
| **Configuration errors** | Validation + staging environment testing |

---

## 🎯 Executive Summary

**Objective:** Implement a resilient, geo-distributed Stockfish engine architecture that automatically routes users to the most efficient engine spot and provides failover within 30 seconds.

**Current Architecture:**
- Single engine endpoint: `http://192.168.40.33:8001`
- Direct HTTP REST calls via `EngineClient` class (103 lines)
- 60-second timeout (needs reduction to 30s)
- No failover mechanism
- Single point of failure

**Target Architecture:**
- Multi-spot engine pool with health monitoring
- Automatic spot selection based on latency/availability
- 30-second timeout with automatic failover
- Graceful degradation under spot failures
- Real-time health metrics and monitoring

---

## 1. Current Situation Analysis

### 1.1 Existing Implementation

**Location:** `backend/core/chess_engine/`

```
backend/core/chess_engine/
├── client.py           (EngineClient - 83 lines)
├── schemas.py          (Data models - 20 lines)
├── exceptions.py       (Custom exceptions)
└── __init__.py
```

**Configuration:** `backend/core/config.py`
```python
ENGINE_URL: str = "http://192.168.40.33:8001"
ENGINE_TIMEOUT: int = 60
```

**Key Components:**
1. **EngineClient** - Single instance, synchronous HTTP calls
2. **analyze()** - Streaming SSE response parser
3. **Error Handling** - ChessEngineError, ChessEngineTimeoutError
4. **Logging** - Dedicated chess_engine.log

### 1.2 Identified Issues

| Issue | Impact | Priority |
|-------|--------|----------|
| Single engine endpoint | No failover | **CRITICAL** |
| 60s timeout | Slow error detection | **HIGH** |
| No health monitoring | Can't predict failures | **HIGH** |
| Synchronous blocking | Poor concurrency | **MEDIUM** |
| No latency tracking | Can't optimize routing | **MEDIUM** |

### 1.3 Requirements

**Functional:**
- Support 2 initial spots (expandable to N)
- Route to most efficient (lowest latency) spot
- Auto-failover within 30 seconds
- Transparent to existing API

**Non-Functional:**
- < 5ms routing overhead
- < 30s failure detection
- 99.5% availability (with 2 spots)
- Zero-downtime configuration updates

---

## 2. Proposed Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Application                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EngineOrchestrator (Facade)                │
│  - Request routing logic                                │
│  - Retry/failover coordination                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 EngineSpotPool                          │
│  - Spot registry & lifecycle                            │
│  - Selection algorithm                                  │
│  - Background health checks                             │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ Spot 1  │         │ Spot 2  │         │ Spot N  │
   │ 33:8001 │         │ 41:5000 │         │ Future  │
   └─────────┘         └─────────┘         └─────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Scope |
|-----------|---------------|-------|
| **EngineOrchestrator** | Public API facade, request routing | 60-80 lines |
| **EngineSpotPool** | Spot management, selection algorithm | 80-100 lines |
| **EngineSpot** | Individual spot client, health tracking | 70-90 lines |
| **SpotHealthMonitor** | Background health checks | 60-80 lines |
| **SpotSelector** | Selection strategy (latency-based) | 40-60 lines |
| **SpotConfig** | Configuration models | 30-40 lines |

---

## 3. Detailed File Structure

### 3.1 New Directory Layout

```
backend/core/chess_engine/
├── __init__.py                 # Export public API
├── client.py                   # [LEGACY] Keep for backward compat
├── schemas.py                  # [KEEP] Existing models
├── exceptions.py               # [KEEP] Existing exceptions
│
├── orchestrator/               # NEW: Multi-spot orchestration
│   ├── __init__.py
│   ├── orchestrator.py         # EngineOrchestrator class (60-80 lines)
│   ├── pool.py                 # EngineSpotPool class (80-100 lines)
│   └── selector.py             # SpotSelector strategy (40-60 lines)
│
├── spot/                       # NEW: Individual spot management
│   ├── __init__.py
│   ├── spot.py                 # EngineSpot class (70-90 lines)
│   ├── health.py               # SpotHealthMonitor (60-80 lines)
│   └── models.py               # SpotConfig, SpotStatus (30-40 lines)
│
└── config/                     # NEW: Configuration
    ├── __init__.py
    └── spots.py                # Spot configuration loader (40-50 lines)
```

**Total Estimated Files:** 14 (including existing 4)
**New Files:** 10
**Maximum Lines per File:** 100 (enforced)

### 3.2 Configuration Files

```
backend/
├── config.py                   # [UPDATE] Add SPOTS config
└── spots.json                  # NEW: Spot definitions (optional)
```

Example `spots.json`:
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
  ],
  "health_check_interval": 30,
  "request_timeout": 30,
  "failover_threshold": 3
}
```

### 3.3 File Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Entry (app.py)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ imports
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          chess_engine/__init__.py (Public API)              │
│          - get_engine() factory                             │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌─────────────────────┐  ┌─────────────────────┐
    │   EngineClient      │  │ EngineOrchestrator  │
    │   (Legacy)          │  │   (New)             │
    └─────────────────────┘  └─────────────────────┘
                                        │
                                        │ uses
                                        ▼
                            ┌─────────────────────┐
                            │   EngineSpotPool    │
                            │   - spot registry   │
                            │   - lifecycle mgmt  │
                            └─────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌─────────────┐    ┌──────────────┐   ┌─────────────┐
            │ EngineSpot  │    │ SpotSelector │   │ SpotHealth  │
            │ (client)    │    │ (algorithm)  │   │ Monitor     │
            └─────────────┘    └──────────────┘   └─────────────┘
                    │                                      │
                    │                                      │
                    └──────────────┬───────────────────────┘
                                   ▼
                           ┌─────────────┐
                           │ SpotModels  │
                           │ SpotConfig  │
                           └─────────────┘
```

### 3.4 File Responsibility Matrix

| File | Primary Responsibility | Dependencies | LOC | Complexity |
|------|----------------------|--------------|-----|------------|
| `orchestrator/orchestrator.py` | Route requests, retry logic | pool, exceptions | 60-80 | Medium |
| `orchestrator/pool.py` | Manage spot lifecycle | spot, selector, health | 80-100 | High |
| `orchestrator/selector.py` | Select best spot | models | 40-60 | Low |
| `spot/spot.py` | Individual spot client | models, schemas | 70-90 | Medium |
| `spot/health.py` | Background health checks | spot, models | 60-80 | Medium |
| `spot/models.py` | Data structures | - | 30-40 | Low |
| `config/spots.py` | Load configuration | models | 40-50 | Low |

---

## 4. Getting Started for Developers

### 4.1 Development Prerequisites

**Skills Required:**
- Python 3.11+ with type hints
- FastAPI / async programming (basic)
- HTTP client libraries (requests, httpx)
- Understanding of health checks and circuit breakers

**Tools Needed:**
```bash
# Python environment
python 3.11+
pip install requests pydantic fastapi

# For testing
pip install pytest pytest-asyncio httpx

# For mock servers (development)
pip install flask  # or any simple HTTP server
```

### 4.2 Quick Start Implementation Guide

**Step 1: Create Directory Structure** (5 minutes)
```bash
cd backend/core/chess_engine
mkdir -p orchestrator spot config
touch orchestrator/__init__.py orchestrator/{orchestrator,pool,selector}.py
touch spot/__init__.py spot/{spot,health,models}.py
touch config/__init__.py config/spots.py
```

**Step 2: Implement Core Models** (30 minutes)
- Start with `spot/models.py` (data structures only, no logic)
- Define `SpotStatus`, `SpotConfig`, `SpotMetrics`

**Step 3: Implement Spot Client** (1-2 hours)
- Create `spot/spot.py` based on existing `client.py`
- Copy-paste analyze() logic, add metrics tracking

**Step 4: Implement Selection Logic** (1 hour)
- Create `orchestrator/selector.py`
- Simple algorithm: filter HEALTHY → sort by latency

**Step 5: Implement Pool** (2 hours)
- Create `orchestrator/pool.py`
- Register spots, lifecycle management

**Step 6: Implement Orchestrator** (2 hours)
- Create `orchestrator/orchestrator.py`
- Retry logic, failover coordination

**Step 7: Add Health Monitor** (2-3 hours)
- Create `spot/health.py`
- Background task with AsyncIO or threading

**Step 8: Integration** (1-2 hours)
- Update `__init__.py`, add feature flag
- Test with existing endpoints

**Total Time Estimate:** 10-15 hours for MVP

### 4.3 Development Tips

**DO:**
- ✅ Copy existing `EngineClient.analyze()` logic for spot client
- ✅ Start without health monitor (add it last)
- ✅ Use feature flag from day 1 (`ENABLE_MULTI_SPOT=false`)
- ✅ Write unit tests for selector algorithm first
- ✅ Log everything during development

**DON'T:**
- ❌ Change existing `EngineClient` (keep for backward compat)
- ❌ Add async/await unless necessary
- ❌ Over-optimize early (simple is better)
- ❌ Skip type hints (Pydantic models help a lot)

---

## 5. Implementation Strategy

### 5.1 Design Principles

1. **Backward Compatibility** - Keep existing `EngineClient` API
2. **Fail-Fast** - 30s timeout, quick failover
3. **Observable** - Rich logging and metrics
4. **Testable** - Clear interfaces, dependency injection
5. **Extensible** - Easy to add new spots/strategies

### 5.2 Key Algorithms

#### Spot Selection Algorithm

```
1. Filter spots by status (HEALTHY only)
2. If no healthy spots → Use DEGRADED spots
3. Sort by:
   - Priority (descending)
   - Average latency (ascending)
   - Success rate (descending)
4. Return top spot
5. If all spots DOWN → Raise ChessEngineError
```

#### Failover Strategy

```
Request Lifecycle:
1. Select best spot (< 1ms)
2. Send request with 30s timeout
3. On timeout/error:
   a. Mark spot as DEGRADED
   b. Get next best spot
   c. Retry (max 2 retries = 3 total spots)
4. On success:
   a. Record latency
   b. Update spot metrics
5. On all spots failed:
   a. Return 503 Service Unavailable
```

#### Health Check Protocol

```
Background Task (every 30s):
1. For each configured spot:
   a. Send lightweight health check (/health endpoint)
   b. Timeout: 5 seconds
   c. On success:
      - Update last_healthy_at
      - Set status = HEALTHY
      - Record response time
   d. On failure:
      - Increment failure_count
      - If failure_count >= 3:
        * Set status = DOWN
      - Else:
        * Set status = DEGRADED
```

---

## 5. Code Templates & Examples

### 5.1 Template: SpotModels (spot/models.py)

```python
"""Data models for multi-spot engine architecture."""
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class SpotStatus(str, Enum):
    """Health status of an engine spot."""
    HEALTHY = "healthy"      # Working normally
    DEGRADED = "degraded"    # Partial failures
    DOWN = "down"            # Unavailable
    UNKNOWN = "unknown"      # Not yet checked


class SpotConfig(BaseModel):
    """Configuration for a single engine spot."""
    id: str = Field(..., description="Unique spot identifier")
    url: str = Field(..., description="Engine HTTP endpoint")
    region: str = Field(default="unknown", description="Geographic region")
    priority: int = Field(default=100, ge=0, le=200, description="Selection priority")
    enabled: bool = Field(default=True, description="Manual enable/disable")


class SpotMetrics(BaseModel):
    """Runtime metrics for a spot."""
    status: SpotStatus
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0  # 0.0 to 1.0
    last_healthy_at: datetime | None = None
    failure_count: int = 0
    total_requests: int = 0

    def update_success(self, latency_ms: float):
        """Record successful request."""
        self.total_requests += 1
        # Rolling average
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.total_requests - 1) + latency_ms)
            / self.total_requests
        )
        self.success_rate = (self.total_requests - self.failure_count) / self.total_requests
        self.last_healthy_at = datetime.utcnow()
        self.status = SpotStatus.HEALTHY

    def update_failure(self):
        """Record failed request."""
        self.total_requests += 1
        self.failure_count += 1
        self.success_rate = (self.total_requests - self.failure_count) / self.total_requests
        # Status managed by health monitor
```

### 5.2 Template: SpotSelector (orchestrator/selector.py)

```python
"""Spot selection algorithm."""
from typing import List
from backend.core.chess_engine.spot.models import SpotConfig, SpotMetrics, SpotStatus


class SpotSelector:
    """Selects the best spot for a request."""

    def select_best(
        self,
        spots: List[tuple[SpotConfig, SpotMetrics]],
    ) -> SpotConfig | None:
        """
        Select best available spot.

        Algorithm:
        1. Filter by status (HEALTHY > DEGRADED > DOWN)
        2. Sort by priority (desc) → latency (asc) → success_rate (desc)
        3. Return top spot

        Returns None if no usable spots.
        """
        # Filter by status priority
        healthy = [(cfg, m) for cfg, m in spots if m.status == SpotStatus.HEALTHY]
        degraded = [(cfg, m) for cfg, m in spots if m.status == SpotStatus.DEGRADED]

        candidates = healthy or degraded
        if not candidates:
            return None

        # Sort by: priority DESC, latency ASC, success_rate DESC
        candidates.sort(
            key=lambda x: (
                -x[0].priority,          # Higher priority first
                x[1].avg_latency_ms,     # Lower latency first
                -x[1].success_rate,      # Higher success rate first
            )
        )

        return candidates[0][0]  # Return SpotConfig
```

### 5.3 Template: EngineSpot (spot/spot.py)

```python
"""Individual spot client (based on existing EngineClient)."""
import time
import requests
from backend.core.chess_engine.schemas import EngineResult
from backend.core.chess_engine.exceptions import ChessEngineError, ChessEngineTimeoutError
from backend.core.chess_engine.spot.models import SpotConfig, SpotMetrics
from backend.core.log.log_chess_engine import logger


class EngineSpot:
    """Client for a single engine spot."""

    def __init__(self, config: SpotConfig, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self.metrics = SpotMetrics(status="unknown")

    def analyze(self, fen: str, depth: int = 15, multipv: int = 3) -> EngineResult:
        """
        Analyze position (copied from EngineClient.analyze).
        Records metrics on success/failure.
        """
        start_time = time.time()
        try:
            # [COPY existing client.py analyze() logic here - lines 26-93]
            # ... SSE parsing logic ...

            # On success: update metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.update_success(latency_ms)
            logger.info(f"[{self.config.id}] Analysis succeeded ({latency_ms:.1f}ms)")
            return result

        except requests.exceptions.Timeout:
            self.metrics.update_failure()
            logger.error(f"[{self.config.id}] Timeout after {self.timeout}s")
            raise ChessEngineTimeoutError(self.timeout)
        except Exception as e:
            self.metrics.update_failure()
            logger.error(f"[{self.config.id}] Request failed: {e}")
            raise ChessEngineError(f"Spot {self.config.id} failed: {e}")

    def health_check(self) -> bool:
        """Quick health check (GET /health)."""
        try:
            resp = requests.get(f"{self.config.url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
```

### 5.4 Template: Factory Function (__init__.py)

```python
"""Chess engine package - multi-spot orchestration."""
from core.config import settings
from .client import EngineClient  # Legacy
from .orchestrator.orchestrator import EngineOrchestrator  # New


def get_engine():
    """
    Factory function for engine client.
    Returns appropriate implementation based on feature flag.
    """
    if settings.ENABLE_MULTI_SPOT:
        return EngineOrchestrator()
    else:
        return EngineClient()  # Legacy single-spot


# Public API
__all__ = ["get_engine", "EngineClient", "EngineOrchestrator"]
```

---

## 6. API Changes & Integration

### 6.1 Public API (Unchanged)

```python
# Existing endpoint (no changes to signature)
POST /analyze
GET /analyze/stream

# Internally routes through EngineOrchestrator
```

### 6.2 New Admin Endpoints

```python
# Monitor spot health
GET /admin/engine/spots
Response: List[SpotMetrics]

# Enable/disable spot
POST /admin/engine/spots/{spot_id}/enable
POST /admin/engine/spots/{spot_id}/disable

# Force health check
POST /admin/engine/spots/{spot_id}/healthcheck
```

---

## 7. Error Handling

### 7.1 Error Types

| Error | Condition | HTTP Status | Retry? |
|-------|-----------|-------------|--------|
| `SpotUnavailableError` | Single spot down | - | Yes (auto) |
| `AllSpotsDownError` | All spots unavailable | 503 | No |
| `SpotTimeoutError` | Spot timeout (>30s) | 503 | Yes (auto) |
| `InvalidFENError` | Bad input | 400 | No |

### 7.2 Retry Logic

```
Max Retries: 2 (total 3 attempts)
Retry Conditions:
  - Timeout (>30s)
  - Connection error
  - 5xx response
  - Empty response

No Retry:
  - 4xx errors (client error)
  - Invalid FEN
  - All spots down
```

---

## 8. Monitoring & Logging

### 8.1 Metrics to Track

**Per-Spot Metrics:**
- Request count (total, success, failure)
- Average latency (p50, p95, p99)
- Availability percentage
- Last healthy timestamp
- Current status (HEALTHY/DEGRADED/DOWN)

**Global Metrics:**
- Total requests
- Failover count
- Average request time (including retries)
- Spot utilization distribution

### 8.2 Logging Strategy

```python
# Request flow
INFO: "Routing request to spot: cn-shanghai"
INFO: "Request succeeded: cn-shanghai (124ms)"
WARN: "Spot timeout: cn-shanghai (30.1s), retrying with cn-local"
ERROR: "All spots failed for request"

# Health checks
INFO: "Health check: cn-shanghai HEALTHY (45ms)"
WARN: "Health check failed: cn-local (3/3 failures) → DOWN"
INFO: "Spot recovered: cn-local DEGRADED → HEALTHY"
```

### 8.3 Log Files

```
backend/logs/
├── chess_engine.log         # [EXISTING] General engine logs
├── spot_health.log          # [NEW] Health check logs
└── spot_routing.log         # [NEW] Request routing logs
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```
tests/chess_engine/orchestrator/
├── test_orchestrator.py     # Request routing logic
├── test_pool.py             # Spot pool management
├── test_selector.py         # Selection algorithm
└── test_spot.py             # Individual spot behavior
```

**Test Cases:**
- Spot selection with various health states
- Failover on timeout
- Health state transitions
- Configuration loading
- Concurrent request handling

### 9.2 Integration Tests

```
tests/integration/
└── test_multi_spot.py       # End-to-end multi-spot tests
```

**Scenarios:**
- Primary spot healthy → Route to primary
- Primary spot down → Failover to secondary
- All spots down → Return 503
- Spot recovery → Resume routing
- Concurrent requests → Load distribution

### 9.3 Load Tests

```python
# Simulate 100 concurrent requests
# Verify failover behavior under load
# Measure latency overhead (<5ms target)
```

---

## 10. Deployment Considerations

### 10.1 Environment Variables

```bash
# Existing
ENGINE_URL=http://192.168.40.33:8001
ENGINE_TIMEOUT=60

# New (alternative to spots.json)
ENGINE_SPOTS='[{"id":"cn-shanghai","url":"http://192.168.40.33:8001"},{"id":"cn-local","url":"http://192.168.40.41:5000"}]'
ENABLE_MULTI_SPOT=true
SPOT_HEALTH_CHECK_INTERVAL=30
SPOT_REQUEST_TIMEOUT=30
```

### 10.2 Migration Path

**Phase 1 - Development (Week 1):**
- Implement core components
- Unit tests
- Local testing with mock spots

**Phase 2 - Staging (Week 2):**
- Deploy with `ENABLE_MULTI_SPOT=false`
- Test with real spots
- Monitor health checks

**Phase 3 - Gradual Rollout (Week 3):**
- Enable multi-spot for 10% traffic
- Monitor metrics (latency, errors)
- Increase to 50%, then 100%

**Phase 4 - Full Production (Week 4):**
- Remove legacy `EngineClient` direct usage
- Enable all admin endpoints
- Document operations procedures

### 10.3 Rollback Plan

```python
# Quick rollback via environment variable
ENABLE_MULTI_SPOT=false  # Falls back to legacy EngineClient

# Or fallback to single spot
ENGINE_SPOTS='[{"id":"primary","url":"http://192.168.40.33:8001"}]'
```

---

## 11. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Routing Overhead** | < 5ms | Time from request to spot call |
| **Failover Time** | < 30s | Time to detect failure + retry |
| **Health Check Latency** | < 5s | Health check timeout |
| **Availability** | > 99.5% | With 2+ healthy spots |
| **P95 Latency** | < 200ms | Including network + compute |

---

## 12. Security Considerations

### 12.1 Authentication

- **Spot-to-Spot:** No auth needed (internal network)
- **Admin Endpoints:** Require JWT token with admin role
- **Configuration:** Validate all spot URLs before use

### 12.2 Input Validation

- Validate FEN strings before routing
- Sanitize spot URLs (prevent SSRF)
- Limit spot count (max 10 spots)
- Rate limit admin endpoints

### 12.3 Secrets Management

```bash
# Store spot URLs in Railway environment variables
# Never commit spots.json with production URLs
# Use Railway secrets for sensitive configs
```

---

## 13. Checklists

### 13.1 Stage 1: Foundation (Days 1-3)

#### Data Models & Configuration
- [ ] Create `backend/core/chess_engine/spot/models.py`
  - [ ] Define `SpotStatus` enum
  - [ ] Define `SpotConfig` model
  - [ ] Define `SpotMetrics` model
  - [ ] Add validation logic
- [ ] Create `backend/core/chess_engine/config/spots.py`
  - [ ] Load spots from environment variable
  - [ ] Load spots from JSON file (optional)
  - [ ] Merge with default configuration
  - [ ] Validate spot URLs
- [ ] Update `backend/core/config.py`
  - [ ] Add `ENABLE_MULTI_SPOT` flag
  - [ ] Add `SPOT_HEALTH_CHECK_INTERVAL`
  - [ ] Add `SPOT_REQUEST_TIMEOUT` (30s)
  - [ ] Add `ENGINE_SPOTS` (JSON string)

#### Core Spot Implementation
- [ ] Create `backend/core/chess_engine/spot/spot.py`
  - [ ] `EngineSpot` class (< 100 lines)
  - [ ] `analyze()` method (similar to EngineClient)
  - [ ] `health_check()` method
  - [ ] `update_metrics()` method
  - [ ] Timeout handling (30s)
  - [ ] Error wrapping
- [ ] Create `backend/core/chess_engine/spot/health.py`
  - [ ] `SpotHealthMonitor` class (< 100 lines)
  - [ ] Background task scheduler
  - [ ] Health check execution
  - [ ] Status state machine
  - [ ] Failure threshold logic (3 strikes)
  - [ ] Logging integration

#### Unit Tests
- [ ] Create `tests/chess_engine/spot/test_spot.py`
  - [ ] Test spot initialization
  - [ ] Test analyze() method
  - [ ] Test health check success/failure
  - [ ] Test metric updates
  - [ ] Test timeout behavior
- [ ] Create `tests/chess_engine/spot/test_health.py`
  - [ ] Test health monitor lifecycle
  - [ ] Test status transitions
  - [ ] Test failure threshold
  - [ ] Test recovery logic

---

### 13.2 Stage 2: Orchestration (Days 4-6)

#### Spot Selection Logic
- [ ] Create `backend/core/chess_engine/orchestrator/selector.py`
  - [ ] `SpotSelector` class (< 60 lines)
  - [ ] `select_best_spot()` method
  - [ ] Filter by status (HEALTHY > DEGRADED > DOWN)
  - [ ] Sort by priority + latency + success rate
  - [ ] Handle no-healthy-spots case
- [ ] Create `backend/core/chess_engine/orchestrator/pool.py`
  - [ ] `EngineSpotPool` class (< 100 lines)
  - [ ] Register spots from config
  - [ ] Get spot by ID
  - [ ] Get all spots
  - [ ] Enable/disable spot
  - [ ] Get spot metrics
  - [ ] Start/stop health monitor

#### Request Routing
- [ ] Create `backend/core/chess_engine/orchestrator/orchestrator.py`
  - [ ] `EngineOrchestrator` class (< 80 lines)
  - [ ] `analyze()` public method (matches EngineClient API)
  - [ ] Retry logic (max 2 retries)
  - [ ] Failover on timeout/error
  - [ ] Success metric tracking
  - [ ] Logging integration
  - [ ] Error aggregation

#### Unit Tests
- [ ] Create `tests/chess_engine/orchestrator/test_selector.py`
  - [ ] Test selection with all HEALTHY
  - [ ] Test selection with mixed states
  - [ ] Test selection with all DOWN
  - [ ] Test priority ordering
  - [ ] Test latency-based selection
- [ ] Create `tests/chess_engine/orchestrator/test_pool.py`
  - [ ] Test spot registration
  - [ ] Test enable/disable
  - [ ] Test health monitor lifecycle
  - [ ] Test concurrent access
- [ ] Create `tests/chess_engine/orchestrator/test_orchestrator.py`
  - [ ] Test successful request routing
  - [ ] Test failover on timeout
  - [ ] Test failover on error
  - [ ] Test all-spots-down error
  - [ ] Test retry exhaustion

---

### 13.3 Stage 3: Integration (Days 7-9)

#### API Integration
- [ ] Update `backend/core/chess_engine/__init__.py`
  - [ ] Export `EngineOrchestrator` as primary API
  - [ ] Keep `EngineClient` for backward compat
  - [ ] Add `get_engine()` factory function
- [ ] Update `backend/app/app.py`
  - [ ] Replace `engine = EngineClient()` with `engine = get_engine()`
  - [ ] Add feature flag check (`ENABLE_MULTI_SPOT`)
  - [ ] Add startup event to initialize health monitor
  - [ ] Add shutdown event to cleanup resources

#### Admin Endpoints
- [ ] Add `GET /admin/engine/spots` endpoint
  - [ ] Return list of all spots with metrics
  - [ ] Require admin authentication
  - [ ] Add response model
- [ ] Add `POST /admin/engine/spots/{spot_id}/enable` endpoint
  - [ ] Enable spot by ID
  - [ ] Return updated status
- [ ] Add `POST /admin/engine/spots/{spot_id}/disable` endpoint
  - [ ] Disable spot by ID
  - [ ] Return updated status
- [ ] Add `POST /admin/engine/spots/{spot_id}/healthcheck` endpoint
  - [ ] Force immediate health check
  - [ ] Return health status

#### Logging Enhancement
- [ ] Create `backend/core/log/log_spot_routing.py`
  - [ ] Dedicated logger for routing decisions
  - [ ] Log spot selection
  - [ ] Log failovers
  - [ ] Log retry attempts
- [ ] Create `backend/core/log/log_spot_health.py`
  - [ ] Dedicated logger for health checks
  - [ ] Log status transitions
  - [ ] Log health check results
  - [ ] Separate file: `spot_health.log`

#### Integration Tests
- [ ] Create `tests/integration/test_multi_spot.py`
  - [ ] Test with 2 healthy spots
  - [ ] Test primary spot down (failover)
  - [ ] Test all spots down (503 error)
  - [ ] Test spot recovery
  - [ ] Test concurrent requests (10+ parallel)
  - [ ] Test health monitor behavior
- [ ] Create `tests/integration/test_backward_compat.py`
  - [ ] Test legacy EngineClient still works
  - [ ] Test feature flag OFF behavior
  - [ ] Test migration scenarios

---

### 13.4 Stage 4: Testing & Validation (Days 10-12)

#### Manual Testing
- [ ] Test with local mock spots
  - [ ] Start 2 mock HTTP servers on different ports
  - [ ] Verify routing to primary
  - [ ] Kill primary, verify failover
  - [ ] Restore primary, verify recovery
- [ ] Test with real spots
  - [ ] Configure `192.168.40.33:8001` and `192.168.40.41:5000`
  - [ ] Send 100 sequential requests
  - [ ] Verify spot utilization
  - [ ] Simulate spot failure (firewall block)
  - [ ] Verify 30s timeout + failover

#### Load Testing
- [ ] Create `tests/load/test_multi_spot_load.py`
  - [ ] 100 concurrent requests
  - [ ] Measure P50/P95/P99 latency
  - [ ] Verify < 5ms routing overhead
  - [ ] Spot distribution analysis
- [ ] Test failover under load
  - [ ] Start with 50 RPS
  - [ ] Kill primary spot mid-test
  - [ ] Verify no dropped requests
  - [ ] Measure failover latency

#### Error Scenario Testing
- [ ] Network errors
  - [ ] Connection refused
  - [ ] Connection timeout
  - [ ] DNS failure
- [ ] Engine errors
  - [ ] Invalid FEN
  - [ ] 500 Internal Server Error
  - [ ] Empty response
  - [ ] Malformed JSON
- [ ] Timeout scenarios
  - [ ] Spot responds at 29s (success)
  - [ ] Spot responds at 31s (timeout + failover)
  - [ ] Both spots timeout (503 error)

#### Documentation
- [ ] Update `README.md`
  - [ ] Document multi-spot feature
  - [ ] Configuration instructions
  - [ ] Environment variable reference
- [ ] Create `docs/MULTI_SPOT_GUIDE.md`
  - [ ] Architecture diagram
  - [ ] Configuration examples
  - [ ] Monitoring guide
  - [ ] Troubleshooting
- [ ] Update API documentation
  - [ ] Document admin endpoints
  - [ ] Update response examples
  - [ ] Error codes reference

---

### 13.5 Stage 5: Deployment (Days 13-15)

#### Pre-Deployment
- [ ] Code review
  - [ ] All files < 100 lines
  - [ ] Type hints complete
  - [ ] Error handling comprehensive
  - [ ] Logging sufficient
- [ ] Update `requirements.txt` (if needed)
  - [ ] Verify no new dependencies required
- [ ] Create `spots.json` template
  - [ ] Example configuration
  - [ ] Comments for each field
- [ ] Create deployment checklist
  - [ ] Environment variables to set
  - [ ] Spot URLs to configure
  - [ ] Health check verification steps

#### Staging Deployment
- [ ] Deploy to staging environment
  - [ ] Set `ENABLE_MULTI_SPOT=false` initially
  - [ ] Configure `ENGINE_SPOTS` environment variable
  - [ ] Verify health monitor starts
- [ ] Verify staging
  - [ ] Check `/admin/engine/spots` endpoint
  - [ ] Verify both spots show HEALTHY
  - [ ] Send test requests
  - [ ] Check logs for routing decisions
- [ ] Enable multi-spot
  - [ ] Set `ENABLE_MULTI_SPOT=true`
  - [ ] Restart application
  - [ ] Verify failover behavior
  - [ ] Run load test

#### Production Deployment
- [ ] Phase 1: Shadow mode (Day 13)
  - [ ] Deploy code with `ENABLE_MULTI_SPOT=false`
  - [ ] Monitor health checks in background
  - [ ] Verify no performance impact
- [ ] Phase 2: Canary rollout (Day 14)
  - [ ] Enable for 10% of traffic
  - [ ] Monitor error rates
  - [ ] Monitor latency (P95 < 200ms)
  - [ ] Check failover logs
- [ ] Phase 3: Full rollout (Day 15)
  - [ ] Increase to 50% traffic
  - [ ] Monitor for 4 hours
  - [ ] Increase to 100% traffic
  - [ ] Monitor for 24 hours
- [ ] Post-deployment verification
  - [ ] Verify spot metrics updating
  - [ ] Check health check intervals
  - [ ] Simulate spot failure
  - [ ] Verify monitoring alerts

---

### 13.6 Stage 6: Operations & Monitoring (Ongoing)

#### Monitoring Setup
- [ ] Set up log aggregation
  - [ ] Forward `spot_routing.log` to monitoring system
  - [ ] Forward `spot_health.log` to monitoring system
  - [ ] Create log parsing rules
- [ ] Create dashboards
  - [ ] Spot health status (HEALTHY/DEGRADED/DOWN)
  - [ ] Request distribution by spot
  - [ ] Failover count (last 24h)
  - [ ] Average latency by spot
  - [ ] Success rate by spot
- [ ] Set up alerts
  - [ ] Alert: Any spot DOWN for > 5 minutes
  - [ ] Alert: All spots DOWN
  - [ ] Alert: Failover rate > 5% (last 1h)
  - [ ] Alert: P95 latency > 500ms

#### Operational Procedures
- [ ] Create runbook: "Spot Down"
  - [ ] Investigate spot health
  - [ ] Disable spot manually if needed
  - [ ] Re-enable after fix
- [ ] Create runbook: "All Spots Down"
  - [ ] Check network connectivity
  - [ ] Check engine service status
  - [ ] Emergency contact procedure
- [ ] Create runbook: "Add New Spot"
  - [ ] Update `ENGINE_SPOTS` config
  - [ ] Restart application
  - [ ] Verify health check
  - [ ] Monitor spot utilization

#### Optimization
- [ ] Analyze latency data
  - [ ] Identify slow spots
  - [ ] Adjust priority values
  - [ ] Consider geographic routing
- [ ] Tune parameters
  - [ ] Health check interval (currently 30s)
  - [ ] Request timeout (currently 30s)
  - [ ] Failure threshold (currently 3)
  - [ ] Retry count (currently 2)

---

## 14. Risk Assessment

### 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Spot selection overhead > 5ms | Low | Medium | Profile and optimize selector |
| Health check storms | Medium | Low | Stagger health checks |
| Failover loops | Low | High | Add cooldown between retries |
| Memory leak in health monitor | Low | High | Proper cleanup, monitoring |
| Race conditions in pool | Medium | Medium | Thread-safe data structures |

### 14.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| All spots down simultaneously | Low | Critical | Multiple geographies, monitoring |
| Configuration error | Medium | High | Validation, staging tests |
| Spot URL changes | Low | Medium | Environment variables, no hardcode |
| Network partition | Low | High | Independent spots, quick failover |

### 14.3 Migration Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing API | Low | Critical | Backward compatibility layer |
| Performance regression | Medium | High | Load testing, gradual rollout |
| Logging overhead | Medium | Low | Async logging, sampling |
| Feature flag not working | Low | Critical | Test both modes thoroughly |

---

## 15. Success Criteria

### 15.1 Functional Requirements ✓

- [ ] Support 2 spots (expandable to N)
- [ ] Route to lowest latency spot
- [ ] Failover within 30 seconds
- [ ] Transparent to existing API
- [ ] Admin endpoints for monitoring

### 15.2 Performance Requirements ✓

- [ ] Routing overhead < 5ms (P95)
- [ ] Request timeout = 30s (configurable)
- [ ] Failover time < 30s
- [ ] Availability > 99.5% (with 2 spots)
- [ ] P95 latency < 200ms

### 15.3 Code Quality Requirements ✓

- [ ] All files < 100 lines
- [ ] 90%+ test coverage
- [ ] Type hints on all public APIs
- [ ] Comprehensive error handling
- [ ] Detailed logging

### 15.4 Operational Requirements ✓

- [ ] Zero-downtime deployment
- [ ] Rollback in < 5 minutes
- [ ] Monitoring dashboards
- [ ] Alerting rules
- [ ] Runbooks for common issues

---

## 16. Future Enhancements

### 16.1 Phase 2 Features (Post-MVP)

1. **Geographic Routing**
   - Detect user location (IP geolocation)
   - Route to nearest spot
   - Fallback to latency-based selection

2. **Load Balancing**
   - Track spot CPU/memory usage
   - Route to least loaded spot
   - Prevent spot overload

3. **Adaptive Timeouts**
   - Learn spot latency distribution
   - Adjust timeout per spot (e.g., 2x P95)
   - Faster failover for slow spots

4. **Caching**
   - Cache analysis results (FEN → EngineResult)
   - TTL: 5 minutes
   - Reduce spot load by 30-50%

5. **WebSocket Support**
   - Persistent connections to spots
   - Reduce connection overhead
   - Real-time analysis streaming

### 16.2 Phase 3 Features (Long-term)

1. **Auto-Scaling**
   - Dynamically add/remove spots
   - Integration with cloud providers
   - Kubernetes deployment

2. **ML-Based Selection**
   - Predict spot performance
   - Learn user patterns
   - Optimize for latency + cost

3. **Multi-Region**
   - Deploy to AWS/Azure/GCP regions
   - Cross-region replication
   - 99.99% availability target

---

## 17. Appendix

### 17.1 Code Size Verification Script

```bash
#!/bin/bash
# verify_file_sizes.sh
find backend/core/chess_engine -name "*.py" | while read file; do
  lines=$(wc -l < "$file")
  if [ $lines -gt 100 ]; then
    echo "ERROR: $file has $lines lines (> 100)"
    exit 1
  else
    echo "OK: $file ($lines lines)"
  fi
done
```

### 17.2 Health Check Endpoint Example

```python
# On engine service (192.168.40.33:8001, 192.168.40.41:5000)
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### 17.3 Sample Configuration

```bash
# Railway Environment Variables
ENABLE_MULTI_SPOT=true
SPOT_REQUEST_TIMEOUT=30
SPOT_HEALTH_CHECK_INTERVAL=30

ENGINE_SPOTS='[
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
```

### 17.4 Sample Admin API Response

```json
GET /admin/engine/spots

{
  "spots": [
    {
      "id": "cn-shanghai",
      "url": "http://192.168.40.33:8001",
      "status": "healthy",
      "metrics": {
        "avg_latency_ms": 124.5,
        "success_rate": 0.998,
        "last_healthy_at": "2026-01-09T10:30:00Z",
        "failure_count": 0,
        "total_requests": 1523
      }
    },
    {
      "id": "cn-local",
      "url": "http://192.168.40.41:5000",
      "status": "degraded",
      "metrics": {
        "avg_latency_ms": 156.2,
        "success_rate": 0.945,
        "last_healthy_at": "2026-01-09T10:25:00Z",
        "failure_count": 2,
        "total_requests": 847
      }
    }
  ],
  "global": {
    "total_requests": 2370,
    "avg_request_time_ms": 135.8,
    "failover_count": 12,
    "uptime_percentage": 99.87
  }
}
```

---

## 18. Quick Implementation Checklist

### Core Implementation (Days 1-7)

**Phase 1: Foundation (2-3 days)**
```
□ Create directory structure (orchestrator/, spot/, config/)
□ Implement spot/models.py (SpotStatus, SpotConfig, SpotMetrics)
□ Implement spot/spot.py (EngineSpot class, copy from client.py)
□ Unit tests for spot client
```

**Phase 2: Orchestration (2-3 days)**
```
□ Implement orchestrator/selector.py (selection algorithm)
□ Implement orchestrator/pool.py (EngineSpotPool)
□ Implement orchestrator/orchestrator.py (retry + failover)
□ Unit tests for selector and orchestrator
```

**Phase 3: Integration (1-2 days)**
```
□ Implement config/spots.py (load from env/JSON)
□ Update __init__.py (get_engine() factory)
□ Update config.py (add ENABLE_MULTI_SPOT flag)
□ Update app.py to use get_engine()
□ Integration tests
```

**Phase 4: Health Monitor (2-3 days)**
```
□ Implement spot/health.py (background health checks)
□ Integrate with pool startup/shutdown
□ Add admin endpoints (GET /admin/engine/spots)
□ Test health check behavior
```

### Testing & Deployment (Days 8-15)

**Manual Testing (2 days)**
```
□ Test with local mock spots
□ Test failover behavior (kill primary spot)
□ Test spot recovery
□ Load test (100 concurrent requests)
```

**Staging Deployment (2 days)**
```
□ Deploy with ENABLE_MULTI_SPOT=false
□ Verify health monitor background task
□ Enable multi-spot, verify routing
□ Monitor logs and metrics
```

**Production Rollout (3 days)**
```
□ Day 1: Shadow mode (feature flag OFF, monitor only)
□ Day 2: Canary (10% → 50% traffic)
□ Day 3: Full rollout (100% traffic)
□ Post-deployment monitoring
```

**Documentation (1 day)**
```
□ Update README.md
□ Create MULTI_SPOT_GUIDE.md
□ Document admin endpoints
□ Create operational runbooks
```

---

## 19. File Creation Checklist

Copy-paste this checklist when starting implementation:

```bash
# Create directories
mkdir -p backend/core/chess_engine/{orchestrator,spot,config}

# Create files
touch backend/core/chess_engine/orchestrator/__init__.py
touch backend/core/chess_engine/orchestrator/orchestrator.py    # 60-80 LOC
touch backend/core/chess_engine/orchestrator/pool.py            # 80-100 LOC
touch backend/core/chess_engine/orchestrator/selector.py        # 40-60 LOC

touch backend/core/chess_engine/spot/__init__.py
touch backend/core/chess_engine/spot/spot.py                    # 70-90 LOC
touch backend/core/chess_engine/spot/health.py                  # 60-80 LOC
touch backend/core/chess_engine/spot/models.py                  # 30-40 LOC

touch backend/core/chess_engine/config/__init__.py
touch backend/core/chess_engine/config/spots.py                 # 40-50 LOC

# Update existing files
# - backend/core/chess_engine/__init__.py (add get_engine factory)
# - backend/core/config.py (add ENABLE_MULTI_SPOT, ENGINE_SPOTS)
# - backend/app/app.py (use get_engine() instead of EngineClient())

# Create test files
mkdir -p tests/chess_engine/{orchestrator,spot,integration}
touch tests/chess_engine/orchestrator/test_{orchestrator,pool,selector}.py
touch tests/chess_engine/spot/test_{spot,health}.py
touch tests/integration/test_multi_spot.py
```

---

## 20. Troubleshooting Guide

### Common Implementation Issues

#### Issue 1: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'backend.core.chess_engine.spot'
```

**Solution:**
- Ensure all `__init__.py` files exist in new directories
- Check Python path includes backend directory
- Verify directory structure matches plan

#### Issue 2: Circular Import

**Symptom:**
```
ImportError: cannot import name 'EngineOrchestrator' from partially initialized module
```

**Solution:**
- Move imports inside functions (lazy loading)
- Use `TYPE_CHECKING` for type hints only
- Check dependency graph (Section 3.3)

#### Issue 3: Health Monitor Not Starting

**Symptom:**
- Health checks never run
- All spots stuck in UNKNOWN status

**Solution:**
- Verify background task registered in app startup
- Check logs for task exceptions
- Test health_check() method independently
```python
# Add to app.py startup
@app.on_event("startup")
async def startup_event():
    engine = get_engine()
    if hasattr(engine, 'pool'):
        engine.pool.start_health_monitor()
```

#### Issue 4: Timeout Not Working

**Symptom:**
- Requests hang longer than 30s
- No failover occurring

**Solution:**
- Check timeout passed to requests.get()
- Verify timeout in seconds (not milliseconds)
- Test with artificially slow endpoint

#### Issue 5: Metrics Not Updating

**Symptom:**
- avg_latency_ms always 0
- success_rate always 1.0

**Solution:**
- Ensure `update_success()` called after requests
- Check metric calculation logic
- Verify no silent exceptions in update methods

#### Issue 6: All Spots Marked DOWN

**Symptom:**
- Health checks failing for all spots
- Spots work when tested manually

**Solution:**
- Verify `/health` endpoint exists on engine services
- Check network connectivity from app server
- Test health check URL manually:
```bash
curl -v http://192.168.40.33:8001/health
```

#### Issue 7: Feature Flag Not Working

**Symptom:**
- `ENABLE_MULTI_SPOT=true` but still using single client

**Solution:**
- Verify environment variable loaded in config.py
- Check `get_engine()` factory logic
- Restart application after env change
```python
# Debug in app.py
from core.config import settings
print(f"Multi-spot enabled: {settings.ENABLE_MULTI_SPOT}")
```

#### Issue 8: Spot Config Parse Error

**Symptom:**
```
ValidationError: invalid JSON in ENGINE_SPOTS
```

**Solution:**
- Validate JSON syntax (use jsonlint.com)
- Ensure proper escaping in environment variables
- Try file-based config instead (spots.json)
```bash
# Validate JSON
echo $ENGINE_SPOTS | python -m json.tool
```

### Performance Issues

#### Issue 9: High Routing Overhead (>10ms)

**Potential Causes:**
- Too many spots (>10)
- Complex selection logic
- Synchronous I/O in selector

**Solutions:**
- Profile with `time` module
- Cache spot list
- Pre-filter disabled spots

#### Issue 10: Memory Leak

**Symptom:**
- Memory usage grows over time
- Application becomes slow

**Potential Causes:**
- Health monitor not cleaning up
- Metrics accumulating unbounded

**Solutions:**
- Add memory profiling (`memory_profiler`)
- Limit metric history (rolling window)
- Ensure proper cleanup in health monitor

### Testing Issues

#### Issue 11: Integration Tests Failing

**Common Causes:**
- Mock spots not started
- Race conditions in health checks
- Hardcoded timeouts too short

**Solutions:**
- Add delays for health check cycles
- Use pytest fixtures for mock servers
- Increase test timeouts for CI

#### Issue 12: Flaky Tests

**Common Causes:**
- Health monitor background task interference
- Timing-dependent assertions
- Shared state between tests

**Solutions:**
- Mock health monitor in unit tests
- Use deterministic time (`freezegun`)
- Reset global state in teardown

### Debug Commands

```bash
# Check spot health
curl http://localhost:8000/admin/engine/spots | jq

# Test analyze endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 10}'

# Monitor logs in real-time
tail -f backend/logs/chess_engine.log
tail -f backend/logs/spot_routing.log

# Test spot directly
curl -v "http://192.168.40.33:8001/analyze/stream?fen=START_FEN&depth=10&multipv=3"
```

---

## 21. Contact & Support

**Implementation Lead:** [Your Name]
**Technical Review:** [Reviewer Name]
**Deployment Owner:** [DevOps Name]

**Timeline:** 15 days (3 weeks)
**Estimated Effort:** 60-80 hours
**Team Size:** 1-2 developers

**Questions?** Open an issue or contact the team lead.

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Last Updated** | 2026-01-09 |
| **Status** | ✅ READY FOR IMPLEMENTATION |
| **Approval** | Required |
| **Complexity** | Medium-High |
| **Risk Level** | Medium |

---

## Quick Navigation

| For... | Go To |
|--------|-------|
| **New Developers** | [§4 Getting Started](#4-getting-started-for-developers) → [§5 Code Templates](#5-code-templates--examples) |
| **System Architects** | [§2 Architecture](#2-proposed-architecture) → [§3 File Structure](#3-detailed-file-structure) |
| **Implementation** | [§18 Quick Checklist](#18-quick-implementation-checklist) → [§19 File Creation](#19-file-creation-checklist) |
| **Testing** | [§9 Testing Strategy](#9-testing-strategy) → [§11 Performance Targets](#11-performance-targets) |
| **Deployment** | [§10 Deployment](#10-deployment-considerations) → [§14 Risk Assessment](#14-risk-assessment) |
| **Debugging** | [§20 Troubleshooting](#20-troubleshooting-guide) |
| **Future Planning** | [§16 Future Enhancements](#16-future-enhancements) |

---

## Summary

This implementation plan provides:
- ✅ Clear file organization (< 100 LOC per file)
- ✅ Step-by-step implementation guide (10-15 hours MVP)
- ✅ Copy-paste code templates
- ✅ Comprehensive testing strategy
- ✅ Production deployment checklist
- ✅ Troubleshooting guide
- ✅ Risk mitigation strategies

**Ready to start?** → Jump to [Getting Started for Developers](#4-getting-started-for-developers)

---

**END OF IMPLEMENTATION PLAN**
