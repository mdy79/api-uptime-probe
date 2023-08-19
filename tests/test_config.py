import pytest
import os
from api_uptime_probe.config import load_config, AppConfig


def test_load_config_valid(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("""
endpoints:
  - id: core-api
    name: Core API Service
    url: https://api.example.com/health
    interval: 15
    timeout: 3
    expected_status: [200, 204]
    failure_threshold: 3
    recovery_threshold: 1

telegram:
  enabled: true
  bot_token: "123456:ABC-DEF"
  chat_id: "-10012345"

discord:
  enabled: false
  webhook_url: null

concurrency_limit: 5
""")

    config = load_config(str(cfg_file))
    assert len(config.endpoints) == 1
    assert config.endpoints[0].id == "core-api"
    assert config.endpoints[0].interval == 15.0
    assert config.endpoints[0].timeout == 3.0
    assert config.endpoints[0].expected_status == [200, 204]
    assert config.telegram.enabled is True
    assert config.telegram.bot_token == "123456:ABC-DEF"
    assert config.discord.enabled is False
    assert config.concurrency_limit == 5


def test_load_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/non/existent/config.yaml")
