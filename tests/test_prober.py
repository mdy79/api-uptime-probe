import pytest
import httpx
import respx
from api_uptime_probe.prober import HttpProber
from api_uptime_probe.config import EndpointConfig
from api_uptime_probe.models import HealthStatus


@pytest.mark.asyncio
async def test_prober_success():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.test") as mock:
            mock.get("/health").respond(200, json={"status": "ok"}, text='{"status":"ok"}')
            prober = HttpProber(client=client)
            ep = EndpointConfig(id="test", name="Test API", url="https://api.test/health", expected_status=[200])

            res = await prober.probe(ep)
            assert res.status == HealthStatus.UP
            assert res.status_code == 200
            assert res.latency_ms > 0
            assert res.error is None


@pytest.mark.asyncio
async def test_prober_status_mismatch():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.test") as mock:
            mock.get("/error").respond(503, text="Service Unavailable")
            prober = HttpProber(client=client)
            ep = EndpointConfig(id="test", name="Test API", url="https://api.test/error", expected_status=[200])

            res = await prober.probe(ep)
            assert res.status == HealthStatus.DOWN
            assert res.status_code == 503
            assert "Unexpected status code 503" in res.error


@pytest.mark.asyncio
async def test_prober_body_contains_assertion():
    async with httpx.AsyncClient() as client:
        with respx.mock(base_url="https://api.test") as mock:
            mock.get("/data").respond(200, text="database is starting up")
            prober = HttpProber(client=client)
            ep = EndpointConfig(
                id="test",
                name="Test API",
                url="https://api.test/data",
                expected_status=[200],
                body_contains="database:ready"
            )

            res = await prober.probe(ep)
            assert res.status == HealthStatus.DOWN
            assert "Body assertion failed" in res.error
