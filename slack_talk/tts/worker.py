"""TTS queue worker service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from slack_talk.core.models import SlackMessage
from slack_talk.core.queue import TTSQueue

logger = logging.getLogger(__name__)


class TTSWorker:
    def __init__(
        self,
        queue: TTSQueue,
        engine: Any,  # TTSEngine or mock
        player: Any,  # AudioPlayer or mock
        retry_count: int = 2,
    ) -> None:
        self._queue = queue
        self._engine = engine
        self._player = player
        self._retry_count = retry_count
        self._last_channel_id: str | None = None

    @property
    def name(self) -> str:
        return "TTSWorker"

    @property
    def last_channel_id(self) -> str | None:
        return self._last_channel_id

    async def start(self) -> None:
        pass  # Engine is started separately

    async def run(self) -> None:
        logger.info("TTSWorker started")
        try:
            while True:
                queued = await self._queue.dequeue()
                await self._process(queued.message)
        except asyncio.CancelledError:
            logger.info("TTSWorker cancelled")

    async def stop(self) -> None:
        logger.info("TTSWorker stopped")

    async def _process(self, message: SlackMessage) -> None:
        text = self._format_for_speech(message)
        logger.info("TTS: %s", text)

        for attempt in range(self._retry_count + 1):
            try:
                audio, sample_rate = await self._engine.synthesize(text)
                await self._player.play(audio, sample_rate)
                self._last_channel_id = message.channel_id
                return
            except Exception:
                if attempt < self._retry_count:
                    logger.warning(
                        "TTS failed (attempt %d/%d), retrying...",
                        attempt + 1,
                        self._retry_count,
                    )
                else:
                    logger.error(
                        "TTS failed after %d retries, skipping: %s",
                        self._retry_count,
                        text[:50],
                    )

    @staticmethod
    def _format_for_speech(message: SlackMessage) -> str:
        if message.is_thread_reply:
            return f"{message.channel_name} スレッド。{message.text}"
        return f"{message.channel_name}。{message.text}"
