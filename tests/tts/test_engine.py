"""Tests for TTS engine."""

import numpy as np
import pytest

from slack_talk.tts.engine import TTSEngine


class TestTTSEngineInterface:
    """TTSEngine が必要なインターフェースを公開していることを検証する。"""

    def test_engine_has_required_methods(self):
        """Verify TTSEngine exposes the expected interface."""
        assert hasattr(TTSEngine, "start")
        assert hasattr(TTSEngine, "synthesize")
        assert hasattr(TTSEngine, "stop")

    def test_engine_has_update_settings(self):
        """Verify TTSEngine exposes update_settings."""
        assert hasattr(TTSEngine, "update_settings")

    def test_engine_has_name_property(self):
        """Verify TTSEngine exposes name property."""
        engine = TTSEngine()
        assert engine.name == "TTSEngine"

    def test_default_sample_rate(self):
        """Verify default sample rate is 24000."""
        engine = TTSEngine()
        assert engine.sample_rate == 24000

    def test_init_with_custom_params(self):
        """Verify TTSEngine accepts custom parameters."""
        engine = TTSEngine(
            reference_audio_path="/tmp/test.wav",
            flow_matching_steps=20,
            volume=0.5,
        )
        assert engine._flow_matching_steps == 20
        assert engine._volume == 0.5

    def test_update_settings(self):
        """Verify update_settings modifies engine parameters."""
        engine = TTSEngine()
        engine.update_settings(volume=0.3, flow_matching_steps=15)
        assert engine._volume == 0.3
        assert engine._flow_matching_steps == 15


class TestTTSEngineSynthesize:
    """Integration tests - require TADA model downloaded.
    Skip in CI with: pytest -m 'not slow'
    """

    @pytest.mark.slow
    async def test_synthesize_returns_audio(self):
        engine = TTSEngine()
        await engine.start()
        try:
            audio, sample_rate = await engine.synthesize("テスト")
            assert isinstance(audio, np.ndarray)
            assert sample_rate > 0
            assert len(audio) > 0
        finally:
            await engine.stop()

    @pytest.mark.slow
    async def test_synthesize_applies_volume(self):
        engine = TTSEngine(volume=0.5)
        await engine.start()
        try:
            audio, _ = await engine.synthesize("テスト")
            # Audio should be scaled by volume
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
        finally:
            await engine.stop()

    @pytest.mark.slow
    async def test_stop_releases_model(self):
        engine = TTSEngine()
        await engine.start()
        await engine.stop()
        assert engine._model is None
        assert engine._encoder is None
