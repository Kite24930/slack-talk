"""Application lifecycle manager."""

from __future__ import annotations

import asyncio
import logging

from slack_talk.core.service import Service

logger = logging.getLogger(__name__)


class App:
    def __init__(self, services: list[Service] | None = None) -> None:
        self._services = services or []

    async def start(self) -> None:
        # Initialize all services sequentially
        for svc in self._services:
            logger.info("Starting service: %s", svc.name)
            await svc.start()

        # Run all services concurrently
        try:
            if self._services:
                async with asyncio.TaskGroup() as tg:
                    for svc in self._services:
                        tg.create_task(svc.run())
        finally:
            # Stop all services in reverse order
            for svc in reversed(self._services):
                logger.info("Stopping service: %s", svc.name)
                try:
                    await svc.stop()
                except Exception:
                    logger.exception("Error stopping %s", svc.name)
