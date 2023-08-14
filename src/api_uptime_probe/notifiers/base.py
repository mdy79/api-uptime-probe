"""Base notifier abstraction."""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import ProbeResult, HealthStatus


class BaseNotifier(ABC):
    @abstractmethod
    async def send_alert(
        self,
        endpoint_id: str,
        endpoint_name: str,
        url: str,
        from_status: HealthStatus,
        to_status: HealthStatus,
        result: ProbeResult,
    ) -> bool:
        pass
