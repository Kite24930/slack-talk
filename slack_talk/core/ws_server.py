"""WebSocket server for Tauri UI communication."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

from websockets.asyncio.server import Server, ServerConnection, broadcast, serve

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class WebSocketServer:
    """WebSocket server that bridges Python backend and Tauri+React frontend.

    Supports broadcasting messages to all connected clients and receiving
    messages from clients via an optional callback handler.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9321,
        on_message: MessageHandler | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._on_message = on_message
        self._server: Server | None = None
        self._clients: set[ServerConnection] = set()

    @property
    def name(self) -> str:
        return "WebSocketServer"

    @property
    def port(self) -> int:
        """Return the actual port the server is listening on."""
        if self._server and self._server.sockets:
            return self._server.sockets[0].getsockname()[1]
        return self._port

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._server = await serve(
            self._handle_client, self._host, self._port
        )
        logger.info("WebSocket server started on ws://%s:%d", self._host, self.port)

    async def run(self) -> None:
        """Run indefinitely until cancelled."""
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the WebSocket server and close all connections."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("WebSocket server stopped")

    async def _handle_client(self, websocket: ServerConnection) -> None:
        """Handle a single client connection."""
        self._clients.add(websocket)
        logger.info("Client connected (%d total)", len(self._clients))
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    if self._on_message:
                        await self._on_message(msg)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from client: %s", str(raw)[:100])
        finally:
            self._clients.discard(websocket)
            logger.info("Client disconnected (%d remaining)", len(self._clients))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        if not self._clients:
            return
        raw = json.dumps(message, ensure_ascii=False)
        broadcast(self._clients, raw)
