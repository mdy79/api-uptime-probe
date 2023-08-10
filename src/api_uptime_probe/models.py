"""Data models for probe execution and state management."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any


class HealthStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"


@dataclass
class ProbeResult:
    endpoint_id: str
    endpoint_name: str
    url: str
    status: HealthStatus
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_success(self) -> bool:
        return self.status == HealthStatus.UP


class ServiceState:
    """Maintains consecutive failure/success counts and state transitions."""

    def __init__(self, endpoint_id: str, failure_threshold: int = 2, recovery_threshold: int = 2):
        self.endpoint_id = endpoint_id
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.current_status: HealthStatus = HealthStatus.UP
        self.consecutive_failures: int = 0
        self.consecutive_successes: int = 0
        self.last_state_change: datetime = datetime.now(timezone.utc)
        self.last_result: Optional[ProbeResult] = None

    def update(self, result: ProbeResult) -> Optional[tuple[HealthStatus, HealthStatus]]:
        """
        Updates state with new result.
        Returns (previous_status, new_status) if a state transition occurred, else None.
        """
        self.last_result = result
        old_status = self.current_status

        if result.is_success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            if self.current_status != HealthStatus.UP and self.consecutive_successes >= self.recovery_threshold:
                self.current_status = HealthStatus.UP
                self.last_state_change = result.timestamp
                return (old_status, HealthStatus.UP)
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            if self.current_status != HealthStatus.DOWN and self.consecutive_failures >= self.failure_threshold:
                self.current_status = HealthStatus.DOWN
                self.last_state_change = result.timestamp
                return (old_status, HealthStatus.DOWN)

        return None
