"""Discord Webhook alert notifier."""

import logging
import httpx
from typing import Optional
from .base import BaseNotifier
from ..models import ProbeResult, HealthStatus

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    def __init__(self, webhook_url: str, client: Optional[httpx.AsyncClient] = None):
        self.webhook_url = webhook_url
        self._external_client = client

    def format_embed(
        self,
        endpoint_id: str,
        endpoint_name: str,
        url: str,
        from_status: HealthStatus,
        to_status: HealthStatus,
        result: ProbeResult,
    ) -> dict:
        color = 0xE02424 if to_status == HealthStatus.DOWN else 0x31C48D
        fields = [
            {"name": "Target URL", "value": f"`{url}`", "inline": False},
            {"name": "Status Transition", "value": f"`{from_status.value}` ➔ `{to_status.value}`", "inline": True},
            {"name": "Latency", "value": f"`{result.latency_ms:.1f}ms`", "inline": True},
        ]
        if result.status_code:
            fields.append({"name": "HTTP Status", "value": str(result.status_code), "inline": True})
        if result.error:
            fields.append({"name": "Reason", "value": f"```{result.error[:500]}```", "inline": False})

        return {
            "title": f"Service Alert: {endpoint_name} is {to_status.value}",
            "color": color,
            "fields": fields,
            "timestamp": result.timestamp.isoformat(),
        }

    async def send_alert(
        self,
        endpoint_id: str,
        endpoint_name: str,
        url: str,
        from_status: HealthStatus,
        to_status: HealthStatus,
        result: ProbeResult,
    ) -> bool:
        embed = self.format_embed(endpoint_id, endpoint_name, url, from_status, to_status, result)
        payload = {
            "username": "API Uptime Monitor",
            "embeds": [embed],
        }

        try:
            if self._external_client:
                resp = await self._external_client.post(self.webhook_url, json=payload, timeout=10.0)
            else:
                async with httpx.AsyncClient() as c:
                    resp = await c.post(self.webhook_url, json=payload, timeout=10.0)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("Failed to send Discord alert: %s", e)
            return False
