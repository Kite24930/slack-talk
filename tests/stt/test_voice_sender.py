"""Tests for voice sender flow."""

import numpy as np
import pytest

from slack_talk.stt.voice_sender import VoiceSender, ConfirmationResult


class FakeRecorder:
    async def record_until_silence(self, **kwargs) -> np.ndarray:
        return np.zeros(16000, dtype=np.float32)


class FakeSTT:
    def __init__(self, text: str = "generalにお疲れ様です"):
        self._text = text

    async def transcribe(self, audio, **kwargs) -> str:
        return self._text


class FakeTTS:
    def __init__(self):
        self.synthesized: list[str] = []

    async def synthesize(self, text: str):
        self.synthesized.append(text)
        return np.zeros(100, dtype=np.float32), 24000


class FakePlayer:
    async def play(self, audio, sample_rate):
        pass


class FakeSlack:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    async def send_message(self, channel_id: str, text: str):
        self.sent.append((channel_id, text))


class TestVoiceSenderParseAndConfirm:
    @pytest.mark.asyncio
    async def test_parse_intent(self):
        sender = VoiceSender(
            recorder=FakeRecorder(),
            stt=FakeSTT("generalにお疲れ様です"),
            tts=FakeTTS(),
            player=FakePlayer(),
            slack=FakeSlack(),
            channel_map={"general": "C1"},
            active_channel_id="C2",
        )
        intent = await sender._record_and_parse()
        assert intent.channel_name == "general"
        assert intent.message == "お疲れ様です"

    @pytest.mark.asyncio
    async def test_fallback_to_active_channel(self):
        sender = VoiceSender(
            recorder=FakeRecorder(),
            stt=FakeSTT("お疲れ様です"),
            tts=FakeTTS(),
            player=FakePlayer(),
            slack=FakeSlack(),
            channel_map={"general": "C1"},
            active_channel_id="C2",
        )
        intent = await sender._record_and_parse()
        assert intent.channel_name is None
