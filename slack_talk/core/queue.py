"""FIFO TTS queue with time-based expiry."""

from __future__ import annotations

import asyncio
import logging
import time

from slack_talk.core.models import QueuedMessage, SlackMessage

logger = logging.getLogger(__name__)


class TTSQueue:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
        self._ttl_seconds = ttl_seconds
        self._skipped_count = 0

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def skipped_count(self) -> int:
        return self._skipped_count

    async def enqueue(self, message: SlackMessage) -> None:
        queued = QueuedMessage(
            message=message,
            enqueued_at=time.time(),
            ttl_seconds=self._ttl_seconds,
        )
        await self._queue.put(queued)

    async def dequeue(self) -> QueuedMessage:
        while True:
            item = await self._queue.get()
            if item.is_expired:
                self._skipped_count += 1
                logger.info(
                    "Skipped expired message: %s (total skipped: %d)",
                    item.message.text[:50],
                    self._skipped_count,
                )
                continue
            return item
