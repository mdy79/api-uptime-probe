import pytest
import httpx
import respx
from api_uptime_probe.prober import HttpProber
from api_uptime_probe.config import EndpointConfig
from api_uptime_probe.models import HealthStatus


@pytest.mark.asyncio
async def test_prober_connect_error():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.unreachable") as mock:
            mock.get("/ping").mock(side_effect=httpx.ConnectError("Connection refused"))
            prober = HttpProber(client=client)
            ep = EndpointConfig(
                id="unreachable",
                name="Unreachable Host",
                url="https://api.unreachable/ping",
            )
            result = await prober.probe(ep)
            assert result.status == HealthStatus.DOWN
            assert "Connection error" in result.error
            assert result.status_code is None


@pytest.mark.asyncio
async def test_prober_timeout_error():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.slow") as mock:
            mock.get("/slow").mock(side_effect=httpx.TimeoutException("Read timed out"))
            prober = HttpProber(client=client)
            ep = EndpointConfig(
                id="slow",
                name="Slow API",
                url="https://api.slow/slow",
                timeout=1.0,
            )
            result = await prober.probe(ep)
            assert result.status == HealthStatus.DOWN
            assert "Request timed out" in result.error
            assert result.status_code is None


@pytest.mark.asyncio
async def test_prober_post_with_headers_and_body():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.test") as mock:
            mock.post("/submit").respond(201, text='{"created": true}')
            prober = HttpProber(client=client)
            ep = EndpointConfig(
                id="submit",
                name="Submit API",
                url="https://api.test/submit",
                method="POST",
                headers={"Authorization": "Bearer secret_token", "X-Custom": "probe"},
                expected_status=[200, 201],
                body_contains="created",
            )
            result = await prober.probe(ep)
            assert result.status == HealthStatus.UP
            assert result.status_code == 201
            assert result.error is None


@pytest.mark.asyncio
async def test_prober_multiple_expected_statuses():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.test") as mock:
            mock.get("/no-content").respond(204)
            prober = HttpProber(client=client)
            ep = EndpointConfig(
                id="no-content",
                name="No Content",
                url="https://api.test/no-content",
                expected_status=[200, 204],
            )
            result = await prober.probe(ep)
            assert result.status == HealthStatus.UP
            assert result.status_code == 204
