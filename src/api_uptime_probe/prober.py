"""Async HTTP prober using httpx."""

import time
import httpx
from typing import Optional
from .models import ProbeResult, HealthStatus
from .config import EndpointConfig


class HttpProber:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._external_client = client

    async def probe(self, endpoint: EndpointConfig) -> ProbeResult:
        start_time = time.perf_counter()
        headers = {
            "User-Agent": "api-uptime-probe/1.0",
            **endpoint.headers,
        }

        async def _do_request(c: httpx.AsyncClient) -> httpx.Response:
            return await c.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                timeout=endpoint.timeout,
                follow_redirects=True,
            )

        try:
            if self._external_client:
                response = await _do_request(self._external_client)
            else:
                async with httpx.AsyncClient(verify=True) as c:
                    response = await _do_request(c)

            latency = (time.perf_counter() - start_time) * 1000.0

            if response.status_code not in endpoint.expected_status:
                return ProbeResult(
                    endpoint_id=endpoint.id,
                    endpoint_name=endpoint.name,
                    url=endpoint.url,
                    status=HealthStatus.DOWN,
                    status_code=response.status_code,
                    latency_ms=latency,
                    error=f"Unexpected status code {response.status_code} (expected {endpoint.expected_status})",
                )

            if endpoint.body_contains and endpoint.body_contains not in response.text:
                return ProbeResult(
                    endpoint_id=endpoint.id,
                    endpoint_name=endpoint.name,
                    url=endpoint.url,
                    status=HealthStatus.DOWN,
                    status_code=response.status_code,
                    latency_ms=latency,
                    error=f"Body assertion failed: keyword '{endpoint.body_contains}' not found",
                )

            return ProbeResult(
                endpoint_id=endpoint.id,
                endpoint_name=endpoint.name,
                url=endpoint.url,
                status=HealthStatus.UP,
                status_code=response.status_code,
                latency_ms=latency,
            )

        except httpx.TimeoutException as exc:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ProbeResult(
                endpoint_id=endpoint.id,
                endpoint_name=endpoint.name,
                url=endpoint.url,
                status=HealthStatus.DOWN,
                latency_ms=latency,
                error=f"Request timed out after {endpoint.timeout}s: {exc}",
            )
        except Exception as exc:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ProbeResult(
                endpoint_id=endpoint.id,
                endpoint_name=endpoint.name,
                url=endpoint.url,
                status=HealthStatus.DOWN,
                latency_ms=latency,
                error=f"Connection error: {str(exc)}",
            )
