"""Tests for VOICEVOX TTS engine."""

import io
import wave

import numpy as np

from slack_talk.tts.voicevox import VoicevoxEngine


class TestVoicevoxEngineInterface:
    def test_has_required_methods(self):
        assert hasattr(VoicevoxEngine, "start")
        assert hasattr(VoicevoxEngine, "synthesize")
        assert hasattr(VoicevoxEngine, "stop")
        assert hasattr(VoicevoxEngine, "update_settings")
        assert hasattr(VoicevoxEngine, "get_speakers")

    def test_has_name_property(self):
        engine = VoicevoxEngine()
        assert engine.name == "VoicevoxEngine"

    def test_default_sample_rate(self):
        engine = VoicevoxEngine()
        assert engine.sample_rate == 24000

    def test_init_with_custom_params(self):
        engine = VoicevoxEngine(
            base_url="http://localhost:50021",
            speaker_id=3,
            volume=0.5,
            speed_scale=1.2,
        )
        assert engine._speaker_id == 3
        assert engine._volume == 0.5

    def test_update_settings(self):
        engine = VoicevoxEngine()
        engine.update_settings(speaker_id=5, volume=0.6, speed_scale=1.5)
        assert engine._speaker_id == 5
        assert engine._volume == 0.6
        assert engine._speed_scale == 1.5

    def test_update_settings_partial(self):
        engine = VoicevoxEngine(speaker_id=1, volume=0.8)
        engine.update_settings(speaker_id=10)
        assert engine._speaker_id == 10
        assert engine._volume == 0.8  # unchanged

    def test_update_settings_base_url_strips_trailing_slash(self):
        engine = VoicevoxEngine()
        engine.update_settings(base_url="http://example.com:50021/")
        assert engine._base_url == "http://example.com:50021"

    def test_wav_to_numpy(self):
        """Test WAV parsing with a minimal valid WAV."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            # Write 100 samples of silence
            wf.writeframes(b"\x00\x00" * 100)
        wav_bytes = buf.getvalue()

        audio = VoicevoxEngine._wav_to_numpy(wav_bytes)
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) == 100

    def test_wav_to_numpy_stereo(self):
        """Test WAV parsing converts stereo to mono."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            # Write 50 stereo frames (100 samples)
            wf.writeframes(b"\x00\x00" * 100)
        wav_bytes = buf.getvalue()

        audio = VoicevoxEngine._wav_to_numpy(wav_bytes)
        assert isinstance(audio, np.ndarray)
        assert len(audio) == 50  # mono: 50 frames

    def test_synthesize_raises_without_start(self):
        """Test that synthesize raises if engine not started."""
        import pytest

        engine = VoicevoxEngine()
        with pytest.raises(RuntimeError, match="Engine not started"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(engine.synthesize("test"))
