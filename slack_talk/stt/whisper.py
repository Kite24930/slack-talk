"""Whisper STT engine with MPS acceleration."""

from __future__ import annotations

import asyncio
import logging
from functools import partial

import numpy as np

logger = logging.getLogger(__name__)


class WhisperSTT:
    def __init__(self, model_name: str = "large") -> None:
        self._model_name = model_name
        self._model = None

    @property
    def name(self) -> str:
        return "WhisperSTT"

    async def start(self) -> None:
        logger.info("Loading Whisper %s model...", self._model_name)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        logger.info("Whisper model loaded")

    def _load_model(self) -> None:
        import whisper

        self._model = whisper.load_model(self._model_name, device="cpu")
        # Note: Whisper's MPS support may require manual device placement
        # Check whisper version for MPS compatibility

    async def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self._transcribe_sync, audio, sample_rate)
        )

    def _transcribe_sync(self, audio: np.ndarray, sample_rate: int) -> str:
        assert self._model is not None, "Model not loaded"
        audio_float = audio.astype(np.float32)
        result = self._model.transcribe(
            audio_float,
            language="ja",
            fp16=False,  # MPS may not support fp16
        )
        return result["text"].strip()

    async def stop(self) -> None:
        self._model = None
        logger.info("WhisperSTT stopped")
