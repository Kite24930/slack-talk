"""Tests for SQLite config manager."""

import os
import tempfile

import pytest

from slack_talk.core.config import ConfigManager
from slack_talk.core.models import AudioSettings, ChannelConfig, DisplaySettings, VoiceSettings


@pytest.fixture
async def config_manager():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    manager = ConfigManager(db_path)
    await manager.initialize()
    yield manager
    await manager.close()
    os.unlink(db_path)


class TestConfigManagerInit:
    async def test_initialize_creates_tables(self, config_manager: ConfigManager):
        # Should not raise
        channels = await config_manager.get_all_channels()
        assert channels == []


class TestChannelConfig:
    async def test_upsert_and_get_channel(self, config_manager: ConfigManager):
        ch = ChannelConfig(channel_id="C123", channel_name="general", tts_enabled=True)
        await config_manager.upsert_channel(ch)
        result = await config_manager.get_channel("C123")
        assert result is not None
        assert result.channel_name == "general"
        assert result.tts_enabled is True

    async def test_get_channel_not_found(self, config_manager: ConfigManager):
        result = await config_manager.get_channel("CXXX")
        assert result is None

    async def test_get_enabled_channels(self, config_manager: ConfigManager):
        await config_manager.upsert_channel(
            ChannelConfig("C1", "general", tts_enabled=True)
        )
        await config_manager.upsert_channel(
            ChannelConfig("C2", "random", tts_enabled=False)
        )
        await config_manager.upsert_channel(
            ChannelConfig("C3", "dev", tts_enabled=True)
        )
        enabled = await config_manager.get_enabled_channels()
        assert len(enabled) == 2
        ids = {ch.channel_id for ch in enabled}
        assert ids == {"C1", "C3"}


class TestAudioSettings:
    async def test_default_audio_settings(self, config_manager: ConfigManager):
        settings = await config_manager.get_audio_settings()
        assert settings.speech_rate == 1.0
        assert settings.volume == 0.8

    async def test_save_and_get_audio_settings(self, config_manager: ConfigManager):
        settings = AudioSettings(speech_rate=1.5, volume=0.6, retry_count=3)
        await config_manager.save_audio_settings(settings)
        result = await config_manager.get_audio_settings()
        assert result.speech_rate == 1.5
        assert result.volume == 0.6
        assert result.retry_count == 3


class TestVoiceSettings:
    async def test_default_voice_settings(self, config_manager: ConfigManager):
        settings = await config_manager.get_voice_settings()
        assert settings.wakeword == "OK Slack"

    async def test_save_and_get_voice_settings(self, config_manager: ConfigManager):
        settings = VoiceSettings(wakeword="Hey Slack", silence_threshold_seconds=2.0)
        await config_manager.save_voice_settings(settings)
        result = await config_manager.get_voice_settings()
        assert result.wakeword == "Hey Slack"
        assert result.silence_threshold_seconds == 2.0


class TestDisplaySettings:
    async def test_default_display_settings(self, config_manager: ConfigManager):
        settings = await config_manager.get_display_settings()
        assert settings.theme == "dark"

    async def test_save_and_get_display_settings(self, config_manager: ConfigManager):
        settings = DisplaySettings(theme="light", thread_preview_count=3)
        await config_manager.save_display_settings(settings)
        result = await config_manager.get_display_settings()
        assert result.theme == "light"
        assert result.thread_preview_count == 3
