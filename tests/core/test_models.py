"""Tests for data models."""

import time

from slack_talk.core.models import (
    AudioSettings,
    ChannelConfig,
    DisplaySettings,
    MessagePriority,
    QueuedMessage,
    SlackMessage,
    VoiceSettings,
    VoiceState,
)


class TestSlackMessage:
    def test_create_normal_message(self):
        msg = SlackMessage(
            channel_id="C123",
            channel_name="general",
            user_id="U456",
            user_name="Taro",
            text="Hello",
            ts="1234567890.123456",
            thread_ts=None,
        )
        assert msg.channel_name == "general"
        assert msg.is_thread_reply is False

    def test_create_thread_reply(self):
        msg = SlackMessage(
            channel_id="C123",
            channel_name="general",
            user_id="U456",
            user_name="Taro",
            text="Reply",
            ts="1234567890.123457",
            thread_ts="1234567890.123456",
        )
        assert msg.is_thread_reply is True


class TestQueuedMessage:
    def test_is_expired_false(self):
        msg = SlackMessage(
            channel_id="C123",
            channel_name="general",
            user_id="U456",
            user_name="Taro",
            text="Hello",
            ts="1234567890.123456",
            thread_ts=None,
        )
        queued = QueuedMessage(message=msg, enqueued_at=time.time(), ttl_seconds=300)
        assert queued.is_expired is False

    def test_is_expired_true(self):
        msg = SlackMessage(
            channel_id="C123",
            channel_name="general",
            user_id="U456",
            user_name="Taro",
            text="Hello",
            ts="1234567890.123456",
            thread_ts=None,
        )
        queued = QueuedMessage(
            message=msg, enqueued_at=time.time() - 400, ttl_seconds=300
        )
        assert queued.is_expired is True


class TestChannelConfig:
    def test_defaults(self):
        ch = ChannelConfig(channel_id="C123", channel_name="general")
        assert ch.tts_enabled is False


class TestAudioSettings:
    def test_defaults(self):
        settings = AudioSettings()
        assert settings.speech_rate == 1.0
        assert settings.volume == 0.8
        assert settings.queue_ttl_seconds == 300
        assert settings.retry_count == 2
        assert settings.flow_matching_steps == 10
        assert settings.reference_audio_path is None


class TestVoiceSettings:
    def test_defaults(self):
        settings = VoiceSettings()
        assert settings.wakeword == "OK Slack"
        assert settings.silence_threshold_seconds == 1.5
        assert settings.input_device is None
        assert settings.output_device is None
        assert settings.default_channel_id is None


class TestVoiceState:
    def test_values(self):
        assert VoiceState.IDLE.value == "idle"
        assert VoiceState.WAKEWORD_DETECTED.value == "wakeword_detected"
        assert VoiceState.RECORDING.value == "recording"
        assert VoiceState.RECOGNIZING.value == "recognizing"
        assert VoiceState.CONFIRMING.value == "confirming"


class TestMessagePriority:
    def test_values(self):
        assert MessagePriority.NORMAL.value == "normal"
        assert MessagePriority.MENTION.value == "mention"
        assert MessagePriority.BOT.value == "bot"
        assert MessagePriority.ERROR.value == "error"


class TestDisplaySettings:
    def test_defaults(self):
        settings = DisplaySettings()
        assert settings.theme == "dark"
        assert settings.thread_preview_count == 2
        assert settings.priority_rules == {}
