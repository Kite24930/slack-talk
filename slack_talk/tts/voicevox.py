"""VOICEVOX TTS engine via local HTTP API."""

from __future__ import annotations

import io
import logging
import wave

import numpy as np

logger = logging.getLogger(__name__)

# Default VOICEVOX engine URL
_DEFAULT_URL = "http://127.0.0.1:50021"


class VoicevoxEngine:
    """VOICEVOX TTS engine.

    Requires VOICEVOX engine running locally on port 50021.
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_URL,
        speaker_id: int = 1,
        volume: float = 0.8,
        speed_scale: float = 1.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._speaker_id = speaker_id
        self._volume = volume
        self._speed_scale = speed_scale
        self._session = None
        self._sample_rate = 24000  # VOICEVOX outputs 24kHz

    @property
    def name(self) -> str:
        return "VoicevoxEngine"

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    async def start(self) -> None:
        import aiohttp

        self._session = aiohttp.ClientSession()
        # Verify VOICEVOX is running
        try:
            async with self._session.get(f"{self._base_url}/version") as resp:
                version = await resp.text()
                logger.info("VOICEVOX engine connected: v%s", version.strip('"'))
        except Exception:
            logger.warning(
                "VOICEVOX engine not reachable at %s. "
                "Make sure VOICEVOX is running.",
                self._base_url,
            )

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """Synthesize text to audio via VOICEVOX HTTP API.

        Parameters
        ----------
        text : str
            Text to synthesize.

        Returns
        -------
        tuple[np.ndarray, int]
            Audio samples as float32 array and sample rate.
        """
        if self._session is None:
            raise RuntimeError("Engine not started. Call start() first.")

        # Step 1: Create audio query
        async with self._session.post(
            f"{self._base_url}/audio_query",
            params={"text": text, "speaker": self._speaker_id},
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"audio_query failed: {resp.status}")
            audio_query = await resp.json()

        # Apply settings
        audio_query["speedScale"] = self._speed_scale
        audio_query["volumeScale"] = self._volume

        # Step 2: Synthesize
        async with self._session.post(
            f"{self._base_url}/synthesis",
            params={"speaker": self._speaker_id},
            json=audio_query,
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"synthesis failed: {resp.status}")
            wav_bytes = await resp.read()

        # Step 3: Parse WAV to numpy
        audio_np = self._wav_to_numpy(wav_bytes)
        return audio_np, self._sample_rate

    @staticmethod
    def _wav_to_numpy(wav_bytes: bytes) -> np.ndarray:
        """Parse WAV bytes to a float32 numpy array normalized to [-1.0, 1.0]."""
        with io.BytesIO(wav_bytes) as buf:
            with wave.open(buf, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                sample_width = wf.getsampwidth()
                n_channels = wf.getnchannels()

        if sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            dtype = np.int16

        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        # Normalize to [-1.0, 1.0]
        audio = audio / np.iinfo(dtype).max

        # Convert to mono if stereo
        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1)

        return audio

    def update_settings(
        self,
        speaker_id: int | None = None,
        volume: float | None = None,
        speed_scale: float | None = None,
        base_url: str | None = None,
    ) -> None:
        """Update engine settings at runtime."""
        if speaker_id is not None:
            self._speaker_id = speaker_id
        if volume is not None:
            self._volume = volume
        if speed_scale is not None:
            self._speed_scale = speed_scale
        if base_url is not None:
            self._base_url = base_url.rstrip("/")

    async def get_speakers(self) -> list[dict]:
        """Get available VOICEVOX speakers."""
        if self._session is None:
            return []
        try:
            async with self._session.get(f"{self._base_url}/speakers") as resp:
                return await resp.json()
        except Exception:
            return []

    async def stop(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("VoicevoxEngine stopped")
