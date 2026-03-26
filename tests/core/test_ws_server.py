"""Tests for WebSocket server."""

import asyncio
import json

import pytest
import websockets

from slack_talk.core.ws_server import WebSocketServer


class TestWebSocketServer:
    @pytest.mark.asyncio
    async def test_start_and_connect(self):
        server = WebSocketServer(host="127.0.0.1", port=0)
        await server.start()
        port = server.port
        assert port > 0

        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            # Server should accept connection
            assert ws.protocol.state.name == "OPEN"

        await server.stop()

    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        server = WebSocketServer(host="127.0.0.1", port=0)
        await server.start()
        port = server.port

        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await asyncio.sleep(0.1)  # Let registration happen
            await server.broadcast({"type": "test", "data": "hello"})
            raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
            msg = json.loads(raw)
            assert msg["type"] == "test"
            assert msg["data"] == "hello"

        await server.stop()

    @pytest.mark.asyncio
    async def test_receive_message_from_client(self):
        received = []

        async def handler(msg: dict) -> None:
            received.append(msg)

        server = WebSocketServer(host="127.0.0.1", port=0, on_message=handler)
        await server.start()
        port = server.port

        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send(json.dumps({"type": "action", "data": "click"}))
            await asyncio.sleep(0.2)

        await server.stop()
        assert len(received) == 1
        assert received[0]["type"] == "action"
