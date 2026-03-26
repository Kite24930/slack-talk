"""Tests for audio I/O."""

import numpy as np
import pytest

from slack_talk.stt.audio import AudioPlayer


class TestAudioPlayerInterface:
    def test_has_required_methods(self):
        assert hasattr(AudioPlayer, "play")
        assert hasattr(AudioPlayer, "list_output_devices")
        assert hasattr(AudioPlayer, "list_input_devices")


class TestListDevices:
    def test_list_output_devices_returns_list(self):
        devices = AudioPlayer.list_output_devices()
        assert isinstance(devices, list)

    def test_list_input_devices_returns_list(self):
        devices = AudioPlayer.list_input_devices()
        assert isinstance(devices, list)
