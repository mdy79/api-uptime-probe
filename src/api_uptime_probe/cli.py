"""CLI entrypoint."""

import argparse
import asyncio
import logging
import signal
import sys
from .config import load_config
from .engine import ProbeEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def main():
    parser = argparse.ArgumentParser(description="Async API Uptime Probe & Alerting Daemon")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        sys.stderr.write(f"Configuration error: {e}\n")
        sys.exit(1)

    engine = ProbeEngine(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown():
        engine.stop()
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass

    try:
        loop.run_until_complete(engine.run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
