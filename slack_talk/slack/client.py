"""Slack Socket Mode client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient

from slack_talk.core.models import SlackMessage

logger = logging.getLogger(__name__)

# Callback type for new messages
MessageCallback = Callable[[SlackMessage], Coroutine[Any, Any, None]]


class SlackListener:
    """Slack Socket Mode listener service."""

    def __init__(
        self,
        bot_token: str,
        app_token: str,
        on_message: MessageCallback | None = None,
    ) -> None:
        self._bot_token = bot_token
        self._app_token = app_token
        self._on_message = on_message
        self._web_client: AsyncWebClient | None = None
        self._socket_client: SocketModeClient | None = None
        self._users: dict[str, str] = {}
        self._channels: dict[str, str] = {}

    @property
    def name(self) -> str:
        return "SlackListener"

    @property
    def users(self) -> dict[str, str]:
        return self._users

    @property
    def channels(self) -> dict[str, str]:
        return self._channels

    async def start(self) -> None:
        self._web_client = AsyncWebClient(token=self._bot_token)
        self._socket_client = SocketModeClient(
            app_token=self._app_token,
            web_client=self._web_client,
        )
        await self._load_users_and_channels()
        logger.info(
            "SlackListener started: %d users, %d channels",
            len(self._users),
            len(self._channels),
        )

    async def _load_users_and_channels(self) -> None:
        assert self._web_client is not None
        # Load users
        try:
            resp = await self._web_client.users_list()
            for member in resp.get("members", []):
                uid = member["id"]
                name = member.get("real_name") or member.get("name", uid)
                self._users[uid] = name
        except Exception:
            logger.exception("Failed to load users")

        # Load channels
        try:
            resp = await self._web_client.conversations_list(
                types="public_channel,private_channel"
            )
            for ch in resp.get("channels", []):
                self._channels[ch["id"]] = ch["name"]
        except Exception:
            logger.exception("Failed to load channels")

    async def run(self) -> None:
        assert self._socket_client is not None
        self._socket_client.socket_mode_request_listeners.append(
            self._handle_socket_event
        )
        await self._socket_client.connect()
        # Keep running until cancelled
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        if self._socket_client:
            await self._socket_client.close()
        logger.info("SlackListener stopped")

    async def _handle_socket_event(self, client: Any, req: Any) -> None:
        if req.type == "events_api":
            event = req.payload.get("event", {})
            if event.get("type") == "message":
                msg = self.parse_message_event(
                    event, self._users, self._channels
                )
                if msg and self._on_message:
                    await self._on_message(msg)
            await req.ack()

    async def send_message(self, channel_id: str, text: str) -> None:
        assert self._web_client is not None
        await self._web_client.chat_postMessage(channel=channel_id, text=text)

    @staticmethod
    def parse_message_event(
        event: dict[str, Any],
        users: dict[str, str],
        channels: dict[str, str],
    ) -> SlackMessage | None:
        """Parse a Slack message event into a SlackMessage.

        Returns None for bot messages, message edits, and other subtypes.
        """
        # Ignore subtypes (bot_message, message_changed, etc.)
        if "subtype" in event:
            return None

        user_id = event.get("user", "")
        if not user_id:
            return None

        channel_id = event.get("channel", "")
        return SlackMessage(
            channel_id=channel_id,
            channel_name=channels.get(channel_id, channel_id),
            user_id=user_id,
            user_name=users.get(user_id, user_id),
            text=event.get("text", ""),
            ts=event.get("ts", ""),
            thread_ts=event.get("thread_ts"),
        )
