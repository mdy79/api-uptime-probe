"""Core async monitoring loop and notification dispatcher."""

import asyncio
import logging
from typing import Dict, List, Optional
from .config import AppConfig, EndpointConfig
from .models import ServiceState, ProbeResult, HealthStatus
from .prober import HttpProber
from .notifiers import BaseNotifier, TelegramNotifier, DiscordNotifier

logger = logging.getLogger(__name__)


class ProbeEngine:
    def __init__(self, config: AppConfig, prober: Optional[HttpProber] = None):
        self.config = config
        self.prober = prober or HttpProber()
        self.states: Dict[str, ServiceState] = {
            ep.id: ServiceState(
                endpoint_id=ep.id,
                failure_threshold=ep.failure_threshold,
                recovery_threshold=ep.recovery_threshold,
            )
            for ep in config.endpoints
        }
        self.notifiers: List[BaseNotifier] = []
        self._setup_notifiers()
        self._running = False
        self._semaphore = asyncio.Semaphore(config.concurrency_limit)

    def _setup_notifiers(self):
        if self.config.telegram.enabled and self.config.telegram.bot_token and self.config.telegram.chat_id:
            self.notifiers.append(
                TelegramNotifier(
                    bot_token=self.config.telegram.bot_token,
                    chat_id=self.config.telegram.chat_id,
                )
            )
        if self.config.discord.enabled and self.config.discord.webhook_url:
            self.notifiers.append(
                DiscordNotifier(
                    webhook_url=self.config.discord.webhook_url,
                )
            )

    async def execute_probe_and_process(self, ep: EndpointConfig) -> tuple[ProbeResult, Optional[tuple[HealthStatus, HealthStatus]]]:
        async with self._semaphore:
            result = await self.prober.probe(ep)

        state = self.states[ep.id]
        transition = state.update(result)

        if transition:
            from_st, to_st = transition
            logger.warning(
                "State transition for '%s' (%s): %s -> %s",
                ep.name, ep.url, from_st.value, to_st.value
            )
            for n in self.notifiers:
                try:
                    await n.send_alert(
                        endpoint_id=ep.id,
                        endpoint_name=ep.name,
                        url=ep.url,
                        from_status=from_st,
                        to_status=to_st,
                        result=result,
                    )
                except Exception as e:
                    logger.error("Notifier %s failed: %s", n.__class__.__name__, e)

        return result, transition

    async def _monitor_endpoint(self, ep: EndpointConfig):
        while self._running:
            try:
                await self.execute_probe_and_process(ep)
            except Exception as e:
                logger.error("Error monitoring %s: %s", ep.id, e)
            await asyncio.sleep(ep.interval)

    async def run(self):
        self._running = True
        logger.info("Starting api-uptime-probe with %d endpoints...", len(self.config.endpoints))
        tasks = [asyncio.create_task(self._monitor_endpoint(ep)) for ep in self.config.endpoints]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self._running = False
            for t in tasks:
                t.cancel()

    def stop(self):
        self._running = False
