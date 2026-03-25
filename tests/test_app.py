"""Tests for Application lifecycle."""

import asyncio

import pytest

from slack_talk.app import App
from slack_talk.core.service import Service


class FakeService(Service):
    def __init__(self, name: str):
        self._name = name
        self.started = False
        self.stopped = False
        self.run_called = False

    @property
    def name(self) -> str:
        return self._name

    async def start(self) -> None:
        self.started = True

    async def run(self) -> None:
        self.run_called = True
        # Simulate short-lived service
        await asyncio.sleep(0.05)

    async def stop(self) -> None:
        self.stopped = True


class TestApp:
    async def test_services_start_and_stop(self):
        svc1 = FakeService("svc1")
        svc2 = FakeService("svc2")
        app = App(services=[svc1, svc2])
        await app.start()
        assert svc1.started is True
        assert svc2.started is True
        assert svc1.run_called is True
        assert svc2.run_called is True
        assert svc1.stopped is True
        assert svc2.stopped is True

    async def test_no_services(self):
        app = App(services=[])
        await app.start()  # Should not raise
