"""Data models for slack-talk."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class VoiceState(Enum):
    IDLE = "idle"
    WAKEWORD_DETECTED = "wakeword_detected"
    RECORDING = "recording"
    RECOGNIZING = "recognizing"
    CONFIRMING = "confirming"


class MessagePriority(Enum):
    NORMAL = "normal"
    MENTION = "mention"
    BOT = "bot"
    ERROR = "error"


@dataclass(frozen=True)
class SlackMessage:
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    text: str
    ts: str
    thread_ts: str | None

    @property
    def is_thread_reply(self) -> bool:
        return self.thread_ts is not None


@dataclass
class QueuedMessage:
    message: SlackMessage
    enqueued_at: float
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.enqueued_at) > self.ttl_seconds


@dataclass
class ChannelConfig:
    channel_id: str
    channel_name: str
    tts_enabled: bool = False


@dataclass
class AudioSettings:
    speech_rate: float = 1.0
    volume: float = 0.8
    queue_ttl_seconds: int = 300
    retry_count: int = 2
    flow_matching_steps: int = 10
    reference_audio_path: str | None = None


@dataclass
class VoiceSettings:
    wakeword: str = "OK Slack"
    silence_threshold_seconds: float = 1.5
    input_device: int | None = None
    output_device: int | None = None
    default_channel_id: str | None = None


@dataclass
class DisplaySettings:
    theme: str = "dark"
    thread_preview_count: int = 2
    priority_rules: dict[str, str] = field(default_factory=dict)
