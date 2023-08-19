from datetime import datetime, timezone
from api_uptime_probe.models import HealthStatus, ProbeResult, ServiceState


def test_service_state_failure_threshold_transition():
    state = ServiceState(endpoint_id="auth-svc", failure_threshold=2, recovery_threshold=2)
    assert state.current_status == HealthStatus.UP

    # First failure -> does not transition yet
    fail1 = ProbeResult("auth-svc", "Auth Service", "http://auth", HealthStatus.DOWN, error="500")
    t1 = state.update(fail1)
    assert t1 is None
    assert state.current_status == HealthStatus.UP
    assert state.consecutive_failures == 1

    # Second failure -> reaches threshold 2 -> transitions to DOWN
    fail2 = ProbeResult("auth-svc", "Auth Service", "http://auth", HealthStatus.DOWN, error="500")
    t2 = state.update(fail2)
    assert t2 == (HealthStatus.UP, HealthStatus.DOWN)
    assert state.current_status == HealthStatus.DOWN


def test_service_state_recovery_transition():
    state = ServiceState(endpoint_id="pay-svc", failure_threshold=1, recovery_threshold=2)

    # Transition to DOWN
    fail = ProbeResult("pay-svc", "Payment", "http://pay", HealthStatus.DOWN)
    state.update(fail)
    assert state.current_status == HealthStatus.DOWN

    # First success -> still DOWN
    ok1 = ProbeResult("pay-svc", "Payment", "http://pay", HealthStatus.UP, status_code=200)
    t1 = state.update(ok1)
    assert t1 is None
    assert state.current_status == HealthStatus.DOWN

    # Second success -> reaches recovery threshold 2 -> transitions to UP
    ok2 = ProbeResult("pay-svc", "Payment", "http://pay", HealthStatus.UP, status_code=200)
    t2 = state.update(ok2)
    assert t2 == (HealthStatus.DOWN, HealthStatus.UP)
    assert state.current_status == HealthStatus.UP
