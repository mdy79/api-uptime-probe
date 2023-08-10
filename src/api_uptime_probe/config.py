"""Configuration management with YAML parsing and env interpolation."""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EndpointConfig:
    id: str
    name: str
    url: str
    method: str = "GET"
    interval: float = 30.0
    timeout: float = 5.0
    expected_status: List[int] = field(default_factory=lambda: [200])
    body_contains: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    failure_threshold: int = 2
    recovery_threshold: int = 2


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


@dataclass
class DiscordConfig:
    enabled: bool = False
    webhook_url: Optional[str] = None


@dataclass
class AppConfig:
    endpoints: List[EndpointConfig] = field(default_factory=list)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    concurrency_limit: int = 10


def load_config(file_path: str) -> AppConfig:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Simple env variable expansion ${VAR:default} or ${VAR}
    expanded = os.path.expandvars(raw_content)
    data = yaml.safe_load(expanded) or {}

    endpoints = []
    for ep in data.get("endpoints", []):
        exp_status = ep.get("expected_status", [200])
        if isinstance(exp_status, int):
            exp_status = [exp_status]
        endpoints.append(
            EndpointConfig(
                id=ep["id"],
                name=ep.get("name", ep["id"]),
                url=ep["url"],
                method=ep.get("method", "GET").upper(),
                interval=float(ep.get("interval", 30.0)),
                timeout=float(ep.get("timeout", 5.0)),
                expected_status=exp_status,
                body_contains=ep.get("body_contains"),
                headers=ep.get("headers", {}),
                failure_threshold=int(ep.get("failure_threshold", 2)),
                recovery_threshold=int(ep.get("recovery_threshold", 2)),
            )
        )

    tg_raw = data.get("telegram", {})
    tg = TelegramConfig(
        enabled=tg_raw.get("enabled", False),
        bot_token=tg_raw.get("bot_token"),
        chat_id=tg_raw.get("chat_id"),
    )

    dc_raw = data.get("discord", {})
    dc = DiscordConfig(
        enabled=dc_raw.get("enabled", False),
        webhook_url=dc_raw.get("webhook_url"),
    )

    return AppConfig(
        endpoints=endpoints,
        telegram=tg,
        discord=dc,
        concurrency_limit=int(data.get("concurrency_limit", 10)),
    )
