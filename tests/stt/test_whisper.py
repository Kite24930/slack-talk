"""Tests for Whisper STT engine."""

import pytest

from slack_talk.stt.whisper import WhisperSTT


class TestWhisperSTTInterface:
    def test_has_required_methods(self):
        assert hasattr(WhisperSTT, "start")
        assert hasattr(WhisperSTT, "transcribe")
        assert hasattr(WhisperSTT, "stop")
