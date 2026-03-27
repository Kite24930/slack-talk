"""Porcupine wakeword detection engine."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

WakeWordCallback = Callable[[], Coroutine[Any, Any, None]]


class WakeWordEngine:
    def __init__(
        self,
        access_key: str,
        keyword_path: str | None = None,
        keywords: list[str] | None = None,
        on_detected: WakeWordCallback | None = None,
    ) -> None:
        self._access_key = access_key
        self._keyword_path = keyword_path
        self._keywords = keywords or ["ok google"]  # Placeholder; custom keyword needed
        self._on_detected = on_detected
        self._porcupine = None
        self._recorder = None
        self._running = False

    @property
    def name(self) -> str:
        return "WakeWordEngine"

    async def start(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._init_porcupine)
        logger.info("WakeWordEngine started")

    def _init_porcupine(self) -> None:
        import pvporcupine
        from pvrecorder import PvRecorder

        if self._keyword_path:
            self._porcupine = pvporcupine.create(
                access_key=self._access_key,
                keyword_paths=[self._keyword_path],
            )
        else:
            self._porcupine = pvporcupine.create(
                access_key=self._access_key,
                keywords=self._keywords,
            )

        self._recorder = PvRecorder(
            frame_length=self._porcupine.frame_length,
        )

    async def run(self) -> None:
        assert self._porcupine is not None
        assert self._recorder is not None

        self._running = True
        self._recorder.start()
        logger.info("Listening for wakeword...")

        loop = asyncio.get_event_loop()
        try:
            while self._running:
                pcm = await loop.run_in_executor(None, self._recorder.read)
                result = self._porcupine.process(pcm)
                if result >= 0:
                    logger.info("Wakeword detected!")
                    if self._on_detected:
                        await self._on_detected()
        except asyncio.CancelledError:
            pass
        finally:
            self._recorder.stop()

    async def stop(self) -> None:
        self._running = False
        if self._recorder:
            self._recorder.stop()
        if self._porcupine:
            self._porcupine.delete()
        logger.info("WakeWordEngine stopped")
