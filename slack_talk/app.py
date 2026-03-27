"""Application lifecycle manager and service wiring."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from slack_talk.core.service import Service

logger = logging.getLogger(__name__)


class App:
    """Application lifecycle manager."""

    def __init__(self, services: list[Service] | None = None) -> None:
        self._services = services or []

    async def start(self) -> None:
        # Initialize all services sequentially
        for svc in self._services:
            logger.info("Starting service: %s", svc.name)
            await svc.start()

        # Run all services concurrently
        try:
            if self._services:
                async with asyncio.TaskGroup() as tg:
                    for svc in self._services:
                        tg.create_task(svc.run())
        finally:
            # Stop all services in reverse order
            for svc in reversed(self._services):
                logger.info("Stopping service: %s", svc.name)
                try:
                    await svc.stop()
                except Exception:
                    logger.exception("Error stopping %s", svc.name)


async def create_app(
    db_path: str = "slack_talk.db",
    ws_port: int = 9321,
) -> App:
    """Create and wire all application services.

    Reads environment variables:
      - SLACK_BOT_TOKEN: Slack Bot User OAuth Token
      - SLACK_APP_TOKEN: Slack App-Level Token (xapp-...)
      - PORCUPINE_ACCESS_KEY: Picovoice access key (optional)

    Parameters
    ----------
    db_path : str
        SQLite データベースファイルのパス。
    ws_port : int
        WebSocket サーバーのポート番号。

    Returns
    -------
    App
        全サービスがワイヤリング済みの App インスタンス。
    """
    from slack_talk.core.config import ConfigManager
    from slack_talk.core.models import SlackMessage
    from slack_talk.core.queue import TTSQueue
    from slack_talk.core.ws_server import WebSocketServer
    from slack_talk.slack.client import SlackListener
    from slack_talk.slack.preprocessor import preprocess
    from slack_talk.stt.audio import AudioPlayer, AudioRecorder
    from slack_talk.stt.voice_sender import VoiceSender
    from slack_talk.stt.wakeword import WakeWordEngine
    from slack_talk.tts.engine import TTSEngine
    from slack_talk.tts.worker import TTSWorker

    # --- Config ---
    config = ConfigManager(db_path)
    await config.initialize()

    audio_settings = await config.get_audio_settings()
    voice_settings = await config.get_voice_settings()

    # --- Slack tokens ---
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    app_token = os.environ.get("SLACK_APP_TOKEN", "")

    # --- TTS Pipeline ---
    tts_queue = TTSQueue(ttl_seconds=audio_settings.queue_ttl_seconds)
    tts_engine = TTSEngine(
        reference_audio_path=audio_settings.reference_audio_path,
        flow_matching_steps=audio_settings.flow_matching_steps,
        volume=audio_settings.volume,
    )
    audio_player = AudioPlayer(output_device=voice_settings.output_device)
    tts_worker = TTSWorker(
        queue=tts_queue,
        engine=tts_engine,
        player=audio_player,
        retry_count=audio_settings.retry_count,
    )

    # --- WebSocket ---
    ws_server = WebSocketServer(port=ws_port)

    # --- Voice Input ---
    audio_recorder = AudioRecorder(
        input_device=voice_settings.input_device,
    )

    # --- TTS-enabled channel tracking ---
    enabled_channels = await config.get_enabled_channels()
    enabled_ids: set[str] = {ch.channel_id for ch in enabled_channels}

    # Forward references populated after construction
    slack_listener: SlackListener | None = None
    voice_sender: VoiceSender | None = None

    # --- Message handler (Slack → Queue + UI) ---
    async def on_slack_message(msg: SlackMessage) -> None:
        """Handle incoming Slack message: forward to UI, enqueue for TTS if enabled."""
        # Forward to UI via WebSocket
        await ws_server.broadcast({
            "type": "message",
            "data": {
                "channel_id": msg.channel_id,
                "channel_name": msg.channel_name,
                "user_id": msg.user_id,
                "user_name": msg.user_name,
                "text": msg.text,
                "ts": msg.ts,
                "thread_ts": msg.thread_ts,
                "is_thread_reply": msg.is_thread_reply,
            },
        })

        # TTS if channel is enabled
        if msg.channel_id in enabled_ids:
            users = slack_listener.users if slack_listener else {}
            channels = slack_listener.channels if slack_listener else {}
            processed_text = preprocess(msg.text, users=users, channels=channels)
            processed_msg = SlackMessage(
                channel_id=msg.channel_id,
                channel_name=msg.channel_name,
                user_id=msg.user_id,
                user_name=msg.user_name,
                text=processed_text,
                ts=msg.ts,
                thread_ts=msg.thread_ts,
            )
            await tts_queue.enqueue(processed_msg)

    # --- Create Slack listener ---
    slack_listener = SlackListener(
        bot_token=bot_token,
        app_token=app_token,
        on_message=on_slack_message,
    )

    # --- WebSocket message handler (UI → Python) ---
    async def on_ws_message(msg: dict[str, Any]) -> None:
        """Handle messages from the Tauri UI via WebSocket."""
        msg_type = msg.get("type", "")
        data = msg.get("data", {})

        if msg_type == "set_active_channel":
            channel_id = data.get("channel_id", "")
            if voice_sender:
                voice_sender.update_active_channel(channel_id)
            logger.info("Active channel set to: %s", channel_id)

        elif msg_type == "toggle_tts":
            from slack_talk.core.models import ChannelConfig

            channel_id = data.get("channel_id", "")
            enabled = data.get("enabled", False)
            channel_name = data.get("channel_name", channel_id)
            await config.upsert_channel(ChannelConfig(
                channel_id=channel_id,
                channel_name=channel_name,
                tts_enabled=enabled,
            ))
            if enabled:
                enabled_ids.add(channel_id)
            else:
                enabled_ids.discard(channel_id)
            logger.info(
                "TTS %s for channel %s",
                "enabled" if enabled else "disabled",
                channel_name,
            )

        elif msg_type == "update_settings":
            await _handle_update_settings(data)

        elif msg_type == "get_channels":
            all_channels = await config.get_all_channels()
            await ws_server.broadcast({
                "type": "channels",
                "data": [
                    {
                        "channel_id": ch.channel_id,
                        "channel_name": ch.channel_name,
                        "tts_enabled": ch.tts_enabled,
                    }
                    for ch in all_channels
                ],
            })

        elif msg_type == "get_settings":
            audio_s = await config.get_audio_settings()
            voice_s = await config.get_voice_settings()
            display_s = await config.get_display_settings()
            await ws_server.broadcast({
                "type": "settings",
                "data": {
                    "audio": {
                        "speech_rate": audio_s.speech_rate,
                        "volume": audio_s.volume,
                        "queue_ttl_seconds": audio_s.queue_ttl_seconds,
                        "retry_count": audio_s.retry_count,
                        "flow_matching_steps": audio_s.flow_matching_steps,
                        "reference_audio_path": audio_s.reference_audio_path,
                    },
                    "voice": {
                        "wakeword": voice_s.wakeword,
                        "silence_threshold_seconds": voice_s.silence_threshold_seconds,
                        "input_device": voice_s.input_device,
                        "output_device": voice_s.output_device,
                        "default_channel_id": voice_s.default_channel_id,
                    },
                    "display": {
                        "theme": display_s.theme,
                        "thread_preview_count": display_s.thread_preview_count,
                        "priority_rules": display_s.priority_rules,
                    },
                },
            })

    async def _handle_update_settings(data: dict[str, Any]) -> None:
        """Process settings update from UI."""
        settings_type = data.get("settings_type", "")
        # Remove meta key before constructing model
        payload = {k: v for k, v in data.items() if k != "settings_type"}

        if settings_type == "audio":
            from slack_talk.core.models import AudioSettings

            new_settings = AudioSettings(**payload)
            await config.save_audio_settings(new_settings)
            tts_engine.update_settings(
                flow_matching_steps=new_settings.flow_matching_steps,
                volume=new_settings.volume,
            )

        elif settings_type == "voice":
            from slack_talk.core.models import VoiceSettings

            new_settings = VoiceSettings(**payload)
            await config.save_voice_settings(new_settings)

        elif settings_type == "display":
            from slack_talk.core.models import DisplaySettings

            new_settings = DisplaySettings(**payload)
            await config.save_display_settings(new_settings)

    ws_server._on_message = on_ws_message

    # --- Voice sender ---
    # channel_map (name -> id) will be populated after SlackListener.start()
    # loads channels from Slack API
    channel_map: dict[str, str] = {}

    voice_sender = VoiceSender(
        recorder=audio_recorder,
        # WhisperSTT is heavy (~1.5GB VRAM). Pass None for now;
        # VoiceSender should lazy-load it on first wakeword detection.
        # TODO: Implement lazy-loading of WhisperSTT in VoiceSender
        stt=None,
        tts=tts_engine,
        player=audio_player,
        slack=slack_listener,
        channel_map=channel_map,
        default_channel_id=voice_settings.default_channel_id,
    )

    # --- Start TTS engine (no run() loop, just needs initialization) ---
    # TTSEngine loads the model which takes time, so start it eagerly.
    await tts_engine.start()

    # --- Build service list ---
    services: list[Any] = [
        slack_listener,
        tts_worker,
        ws_server,
    ]

    # WakeWordEngine is optional (requires PORCUPINE_ACCESS_KEY)
    porcupine_key = os.environ.get("PORCUPINE_ACCESS_KEY", "")
    if porcupine_key:
        wakeword_engine = WakeWordEngine(
            access_key=porcupine_key,
            on_detected=voice_sender.handle_wakeword,
        )
        services.append(wakeword_engine)
        logger.info("WakeWord engine enabled")
    else:
        logger.info("WakeWord engine disabled (no PORCUPINE_ACCESS_KEY)")

    return App(services=services)
