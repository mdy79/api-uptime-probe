# api-uptime-probe

[![CI](https://github.com/mdy79/api-uptime-probe/actions/workflows/ci.yml/badge.svg)](https://github.com/mdy79/api-uptime-probe/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Asynchronous, lightweight, high-reliability HTTP API uptime monitor and service health prober built on Python `asyncio` and `httpx`. Dispatches instant alerts via Telegram Bot API and Discord Webhooks when services transition between healthy and degraded states.

---

## Features

- **Concurrent Async Probing**: Built on `httpx.AsyncClient` with configurable concurrency semaphores to monitor hundreds of endpoints with minimal system resources.
- **Flapping Prevention**: Configurable `failure_threshold` and `recovery_threshold` to avoid false alarms during transient network hiccups.
- **Deep Health Assertions**:
  - HTTP Status Code validation (single or range list, e.g. `[200, 204]`)
  - Substring body assertions (e.g. check for `"status":"healthy"` or DB connectivity tokens)
  - Custom headers (Authorization tokens, tenant routing headers)
- **Multi-Channel Alert Dispatching**:
  - **Telegram Bot**: Markdown-formatted incident notifications with latency, timestamp, and error details.
  - **Discord Webhook**: Color-coded rich embeds (Red for outages, Green for recovery).
- **Production Container**: Small footprint Docker image with non-root security boundaries and Docker Compose support.

---

## Architecture

```
                  +--------------------------+
                  |    Probe Engine (async)  |
                  +-------------+------------+
                                |
             +------------------+------------------+
             |                                     |
   GET /health (HTTPX)                   GET /api/v1/ping (HTTPX)
             v                                     v
   +--------------------+                +--------------------+
   |   Microservice A   |                |   Database API     |
   +--------------------+                +--------------------+
             |                                     |
             +------------------+------------------+
                                |
                   State Transition (UP <-> DOWN)
                                |
            +-------------------+-------------------+
            |                                       |
            v                                       v
   +--------------------+                  +--------------------+
   | Telegram Bot API   |                  |  Discord Webhook   |
   +--------------------+                  +--------------------+
```

---

## Configuration (`config.yaml`)

```yaml
endpoints:
  - id: core-api
    name: "Production Gateway"
    url: "https://api.example.com/health"
    interval: 30
    timeout: 5
    expected_status: [200]
    failure_threshold: 2
    recovery_threshold: 2

  - id: auth-service
    name: "OAuth2 Provider"
    url: "https://auth.example.com/.well-known/jwks.json"
    interval: 15
    timeout: 3
    body_contains: "keys"
    failure_threshold: 3
    recovery_threshold: 1

telegram:
  enabled: true
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"

discord:
  enabled: true
  webhook_url: "${DISCORD_WEBHOOK_URL}"

concurrency_limit: 20
```

---

## Quick Start

### 1. Using Docker Compose

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your endpoints and alert tokens

docker-compose up -d
```

### 2. Manual Installation

```bash
git clone https://github.com/mdy79/api-uptime-probe.git
cd api-uptime-probe
pip install .

api-uptime-probe -c config.yaml
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

## License

MIT © Mehrad Dadgar
