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
    status: SpotStatus = SpotStatus.UNKNOWN
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0  # 0.0 to 1.0
    last_healthy_at: datetime | None = None
    failure_count: int = 0
    total_requests: int = 0

    def update_success(self, latency_ms: float):
        """Record successful request."""
        self.total_requests += 1
        # Rolling average
        if self.total_requests == 1:
            self.avg_latency_ms = latency_ms
        else:
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
        # Status is managed by health monitor, not here
