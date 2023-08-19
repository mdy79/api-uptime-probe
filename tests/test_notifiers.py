import pytest
import httpx
import respx
from api_uptime_probe.models import HealthStatus, ProbeResult
from api_uptime_probe.notifiers import TelegramNotifier, DiscordNotifier


@pytest.mark.asyncio
async def test_telegram_notifier():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.telegram.org") as mock:
            mock.post("/botTEST_TOKEN/sendMessage").respond(200, json={"ok": True})
            notifier = TelegramNotifier("TEST_TOKEN", "-100123", client=client)

            result = ProbeResult(
                endpoint_id="api-1",
                endpoint_name="API Gateway",
                url="https://api.example.com",
                status=HealthStatus.DOWN,
                status_code=502,
                latency_ms=120.5,
                error="Bad Gateway",
            )

            sent = await notifier.send_alert(
                endpoint_id="api-1",
                endpoint_name="API Gateway",
                url="https://api.example.com",
                from_status=HealthStatus.UP,
                to_status=HealthStatus.DOWN,
                result=result,
            )
            assert sent is True


@pytest.mark.asyncio
async def test_discord_notifier():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://discord.com") as mock:
            mock.post("/api/webhooks/123/xyz").respond(204)
            notifier = DiscordNotifier("https://discord.com/api/webhooks/123/xyz", client=client)

            result = ProbeResult(
                endpoint_id="api-1",
                endpoint_name="API Gateway",
                url="https://api.example.com",
                status=HealthStatus.UP,
                status_code=200,
                latency_ms=45.2,
            )

            sent = await notifier.send_alert(
                endpoint_id="api-1",
                endpoint_name="API Gateway",
                url="https://api.example.com",
                from_status=HealthStatus.DOWN,
                to_status=HealthStatus.UP,
                result=result,
            )
            assert sent is True
