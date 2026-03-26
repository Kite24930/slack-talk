"""Tests for TTS queue worker."""

import asyncio
import time

import numpy as np
import pytest

from slack_talk.core.models import SlackMessage
from slack_talk.core.queue import TTSQueue
from slack_talk.tts.worker import TTSWorker


class FakeTTSEngine:
    def __init__(self):
        self.synthesized: list[str] = []

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        self.synthesized.append(text)
        return np.zeros(100, dtype=np.float32), 24000


class FakeAudioPlayer:
    def __init__(self):
        self.played_count = 0

    async def play(self, audio: np.ndarray, sample_rate: int) -> None:
        self.played_count += 1


def _make_message(text: str, channel: str = "general") -> SlackMessage:
    return SlackMessage(
        channel_id="C123",
        channel_name=channel,
        user_id="U456",
        user_name="Taro",
        text=text,
        ts=str(time.time()),
        thread_ts=None,
    )


class TestTTSWorker:
    @pytest.mark.asyncio
    async def test_processes_message_from_queue(self):
        queue = TTSQueue(ttl_seconds=300)
        engine = FakeTTSEngine()
        player = FakeAudioPlayer()
        worker = TTSWorker(queue=queue, engine=engine, player=player, retry_count=2)

        await queue.enqueue(_make_message("hello"))

        # Run worker with a timeout
        task = asyncio.create_task(worker.run())
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(engine.synthesized) == 1
        assert "general" in engine.synthesized[0]
        assert "hello" in engine.synthesized[0]
        assert player.played_count == 1

    @pytest.mark.asyncio
    async def test_formats_thread_reply(self):
        queue = TTSQueue(ttl_seconds=300)
        engine = FakeTTSEngine()
        player = FakeAudioPlayer()
        worker = TTSWorker(queue=queue, engine=engine, player=player, retry_count=2)

        msg = SlackMessage(
            channel_id="C123",
            channel_name="general",
            user_id="U456",
            user_name="Taro",
            text="reply text",
            ts="123.456",
            thread_ts="123.000",
        )
        await queue.enqueue(msg)

        task = asyncio.create_task(worker.run())
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert "スレッド" in engine.synthesized[0]
