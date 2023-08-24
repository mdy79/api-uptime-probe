import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from api_uptime_probe.config import AppConfig, EndpointConfig, TelegramConfig, DiscordConfig
from api_uptime_probe.models import HealthStatus, ProbeResult
from api_uptime_probe.engine import ProbeEngine


@pytest.fixture
def sample_config():
    return AppConfig(
        concurrency_limit=2,
        endpoints=[
            EndpointConfig(
                id="api-auth",
                name="Auth Service",
                url="https://auth.internal/health",
                failure_threshold=2,
                recovery_threshold=2,
                interval=1.0,
            ),
            EndpointConfig(
                id="api-billing",
                name="Billing Service",
                url="https://billing.internal/health",
                failure_threshold=1,
                recovery_threshold=1,
                interval=1.0,
            ),
        ],
        telegram=TelegramConfig(enabled=True, bot_token="token_xyz", chat_id="chat_123"),
        discord=DiscordConfig(enabled=True, webhook_url="https://discord.com/api/webhooks/xyz"),
    )


def test_engine_setup_notifiers(sample_config):
    engine = ProbeEngine(sample_config)
    assert len(engine.notifiers) == 2
    notifier_types = [type(n).__name__ for n in engine.notifiers]
    assert "TelegramNotifier" in notifier_types
    assert "DiscordNotifier" in notifier_types


def test_engine_setup_notifiers_disabled():
    cfg = AppConfig(
        concurrency_limit=2,
        endpoints=[],
        telegram=TelegramConfig(enabled=False, bot_token="token", chat_id="123"),
        discord=DiscordConfig(enabled=False, webhook_url="https://discord.com/xyz"),
    )
    engine = ProbeEngine(cfg)
    assert len(engine.notifiers) == 0


@pytest.mark.asyncio
async def test_engine_execute_probe_transition_and_alerts(sample_config):
    prober_mock = MagicMock()
    engine = ProbeEngine(sample_config, prober=prober_mock)

    mock_notifier = MagicMock()
    mock_notifier.send_alert = AsyncMock()
    engine.notifiers = [mock_notifier]

    ep = sample_config.endpoints[0]  # failure_threshold=2

    # Probe 1: Down (failures=1, threshold=2 -> no transition yet)
    fail_res1 = ProbeResult(
        endpoint_id=ep.id,
        endpoint_name=ep.name,
        url=ep.url,
        status=HealthStatus.DOWN,
        latency_ms=10.0,
        error="Connection refused",
    )
    prober_mock.probe = AsyncMock(return_value=fail_res1)

    res, transition = await engine.execute_probe_and_process(ep)
    assert res == fail_res1
    assert transition is None
    mock_notifier.send_alert.assert_not_called()

    # Probe 2: Down (failures=2, threshold=2 -> transition UP -> DOWN)
    fail_res2 = ProbeResult(
        endpoint_id=ep.id,
        endpoint_name=ep.name,
        url=ep.url,
        status=HealthStatus.DOWN,
        latency_ms=12.0,
        error="Connection refused",
    )
    prober_mock.probe = AsyncMock(return_value=fail_res2)

    res, transition = await engine.execute_probe_and_process(ep)
    assert transition == (HealthStatus.UP, HealthStatus.DOWN)
    mock_notifier.send_alert.assert_called_once_with(
        endpoint_id="api-auth",
        endpoint_name="Auth Service",
        url="https://auth.internal/health",
        from_status=HealthStatus.UP,
        to_status=HealthStatus.DOWN,
        result=fail_res2,
    )


@pytest.mark.asyncio
async def test_engine_notifier_exception_does_not_break_probe(sample_config):
    prober_mock = MagicMock()
    engine = ProbeEngine(sample_config, prober=prober_mock)

    failing_notifier = MagicMock()
    failing_notifier.send_alert = AsyncMock(side_effect=RuntimeError("Discord API 500"))
    engine.notifiers = [failing_notifier]

    ep = sample_config.endpoints[1]  # failure_threshold=1
    fail_res = ProbeResult(
        endpoint_id=ep.id,
        endpoint_name=ep.name,
        url=ep.url,
        status=HealthStatus.DOWN,
        latency_ms=15.0,
        error="Crash",
    )
    prober_mock.probe = AsyncMock(return_value=fail_res)

    res, transition = await engine.execute_probe_and_process(ep)
    assert transition == (HealthStatus.UP, HealthStatus.DOWN)
    failing_notifier.send_alert.assert_called_once()


@pytest.mark.asyncio
async def test_engine_stop():
    cfg = AppConfig(
        concurrency_limit=2,
        endpoints=[EndpointConfig(id="ep1", name="EP 1", url="http://local/test", interval=0.01)],
        telegram=TelegramConfig(enabled=False),
        discord=DiscordConfig(enabled=False),
    )
    prober = MagicMock()
    prober.probe = AsyncMock(
        return_value=ProbeResult(
            endpoint_id="ep1",
            endpoint_name="EP 1",
            url="http://local/test",
            status=HealthStatus.UP,
            latency_ms=5.0,
        )
    )
    engine = ProbeEngine(cfg, prober=prober)

    task = asyncio.create_task(engine.run())
    await asyncio.sleep(0.05)
    assert engine._running is True
    engine.stop()
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert engine._running is False
