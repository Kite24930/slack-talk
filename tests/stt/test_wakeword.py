"""Tests for wakeword engine."""

import pytest

from slack_talk.stt.wakeword import WakeWordEngine


class TestWakeWordEngineInterface:
    def test_has_required_methods(self):
        assert hasattr(WakeWordEngine, "start")
        assert hasattr(WakeWordEngine, "run")
        assert hasattr(WakeWordEngine, "stop")
