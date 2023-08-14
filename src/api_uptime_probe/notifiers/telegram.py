"""Telegram Bot API alert notifier."""

import logging
import httpx
from typing import Optional
from .base import BaseNotifier
from ..models import ProbeResult, HealthStatus

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    def __init__(self, bot_token: str, chat_id: str, client: Optional[httpx.AsyncClient] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._external_client = client
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def format_message(
        self,
        endpoint_id: str,
        endpoint_name: str,
        url: str,
        from_status: HealthStatus,
        to_status: HealthStatus,
        result: ProbeResult,
    ) -> str:
        icon = "🔴" if to_status == HealthStatus.DOWN else "🟢"
        title = f"{icon} *Service Alert: {endpoint_name} is {to_status.value}*"
        lines = [
            title,
            f"*URL:* `{url}`",
            f"*State Change:* `{from_status.value}` ➔ `{to_status.value}`",
            f"*Latency:* `{result.latency_ms:.1f}ms`",
        ]
        if result.status_code:
            lines.append(f"*Status Code:* `{result.status_code}`")
        if result.error:
            lines.append(f"*Details:* `{result.error}`")
        lines.append(f"*Timestamp:* `{result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}`")
        return "\n".join(lines)

    async def send_alert(
        self,
        endpoint_id: str,
        endpoint_name: str,
        url: str,
        from_status: HealthStatus,
        to_status: HealthStatus,
        result: ProbeResult,
    ) -> bool:
        message = self.format_message(endpoint_id, endpoint_name, url, from_status, to_status, result)
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            if self._external_client:
                resp = await self._external_client.post(self.api_url, json=payload, timeout=10.0)
            else:
                async with httpx.AsyncClient() as c:
                    resp = await c.post(self.api_url, json=payload, timeout=10.0)
            return resp.status_code == 200
        except Exception as e:
            logger.error("Failed to send Telegram alert: %s", e)
            return False
