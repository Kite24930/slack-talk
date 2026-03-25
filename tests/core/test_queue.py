"""Tests for FIFO queue manager."""

import asyncio
import time

import pytest

from slack_talk.core.models import QueuedMessage, SlackMessage
from slack_talk.core.queue import TTSQueue


def _make_message(text: str = "hello", channel: str = "general") -> SlackMessage:
    return SlackMessage(
        channel_id="C123",
        channel_name=channel,
        user_id="U456",
        user_name="Taro",
        text=text,
        ts=str(time.time()),
        thread_ts=None,
    )


class TestTTSQueue:
    async def test_enqueue_and_dequeue(self):
        q = TTSQueue(ttl_seconds=300)
        msg = _make_message("hello")
        await q.enqueue(msg)
        result = await asyncio.wait_for(q.dequeue(), timeout=1.0)
        assert result.message.text == "hello"

    async def test_fifo_order(self):
        q = TTSQueue(ttl_seconds=300)
        await q.enqueue(_make_message("first"))
        await q.enqueue(_make_message("second"))
        r1 = await asyncio.wait_for(q.dequeue(), timeout=1.0)
        r2 = await asyncio.wait_for(q.dequeue(), timeout=1.0)
        assert r1.message.text == "first"
        assert r2.message.text == "second"

    async def test_expired_message_skipped(self):
        q = TTSQueue(ttl_seconds=1)
        msg = _make_message("old")
        # Manually enqueue with old timestamp
        queued = QueuedMessage(message=msg, enqueued_at=time.time() - 10, ttl_seconds=1)
        await q._queue.put(queued)
        await q.enqueue(_make_message("new"))
        result = await asyncio.wait_for(q.dequeue(), timeout=1.0)
        assert result.message.text == "new"
        assert q.skipped_count == 1

    async def test_size(self):
        q = TTSQueue(ttl_seconds=300)
        assert q.size == 0
        await q.enqueue(_make_message())
        assert q.size == 1
