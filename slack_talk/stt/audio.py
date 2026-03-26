"""Audio input/output via sounddevice."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    index: int
    name: str
    channels: int


class AudioPlayer:
    def __init__(self, output_device: int | None = None) -> None:
        self._output_device = output_device

    async def play(self, audio: np.ndarray, sample_rate: int) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._play_sync, audio, sample_rate)

    def _play_sync(self, audio: np.ndarray, sample_rate: int) -> None:
        sd.play(audio, samplerate=sample_rate, device=self._output_device)
        sd.wait()

    @staticmethod
    def list_output_devices() -> list[AudioDevice]:
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d["max_output_channels"] > 0:
                result.append(
                    AudioDevice(
                        index=i,
                        name=d["name"],
                        channels=d["max_output_channels"],
                    )
                )
        return result

    @staticmethod
    def list_input_devices() -> list[AudioDevice]:
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                result.append(
                    AudioDevice(
                        index=i,
                        name=d["name"],
                        channels=d["max_input_channels"],
                    )
                )
        return result


class AudioRecorder:
    def __init__(
        self,
        input_device: int | None = None,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> None:
        self._input_device = input_device
        self._sample_rate = sample_rate
        self._channels = channels

    async def record_until_silence(
        self,
        silence_threshold_seconds: float = 1.5,
        energy_threshold: float = 0.01,
    ) -> np.ndarray:
        """Record audio until silence is detected (VAD)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._record_until_silence_sync,
            silence_threshold_seconds,
            energy_threshold,
        )

    def _record_until_silence_sync(
        self,
        silence_threshold_seconds: float,
        energy_threshold: float,
    ) -> np.ndarray:
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(self._sample_rate * chunk_duration)
        silence_chunks_needed = int(silence_threshold_seconds / chunk_duration)

        recorded_chunks: list[np.ndarray] = []
        silent_chunks = 0

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            device=self._input_device,
            dtype="float32",
        ) as stream:
            while True:
                chunk, _ = stream.read(chunk_samples)
                recorded_chunks.append(chunk.copy())

                energy = np.sqrt(np.mean(chunk**2))
                if energy < energy_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                if silent_chunks >= silence_chunks_needed:
                    break

        return np.concatenate(recorded_chunks, axis=0).flatten()
