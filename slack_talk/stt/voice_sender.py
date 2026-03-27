"""Voice send flow orchestrator."""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any

from slack_talk.stt.intent import IntentParser, SendIntent

logger = logging.getLogger(__name__)


class ConfirmationResult(Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class VoiceSender:
    def __init__(
        self,
        recorder: Any,
        stt: Any,
        tts: Any,
        player: Any,
        slack: Any,
        channel_map: dict[str, str],  # name -> id
        active_channel_id: str | None = None,
        default_channel_id: str | None = None,
    ) -> None:
        self._recorder = recorder
        self._stt = stt
        self._tts = tts
        self._player = player
        self._slack = slack
        self._channel_map = channel_map
        self._active_channel_id = active_channel_id
        self._default_channel_id = default_channel_id
        self._intent_parser = IntentParser(known_channels=set(channel_map.keys()))

        # Confirmation keywords
        self._confirm_words = {"はい", "うん", "OK", "オーケー", "送って", "送信"}
        self._cancel_words = {"キャンセル", "やめて", "いいえ", "やめる", "取り消し"}

    def update_active_channel(self, channel_id: str) -> None:
        self._active_channel_id = channel_id

    def update_channel_map(self, channel_map: dict[str, str]) -> None:
        self._channel_map = channel_map
        self._intent_parser.update_channels(set(channel_map.keys()))

    async def handle_wakeword(self) -> None:
        """Full voice send flow triggered by wakeword detection."""
        try:
            # 1. Record and parse intent
            intent = await self._record_and_parse()

            # 2. Resolve channel
            channel_id = self._resolve_channel(intent)
            if not channel_id:
                logger.warning("Could not resolve channel for: %s", intent)
                await self._speak("送信先チャンネルが見つかりません")
                return

            channel_name = intent.channel_name or "アクティブチャンネル"

            # 3. Confirmation
            await self._speak(
                f"{channel_name}に「{intent.message}」を送信します。よろしいですか？"
            )

            result = await self._listen_for_confirmation()

            if result == ConfirmationResult.CONFIRMED:
                await self._slack.send_message(channel_id, intent.message)
                await self._speak("送信しました")
                logger.info("Message sent to %s: %s", channel_name, intent.message)
            else:
                await self._speak("キャンセルしました")
                logger.info("Send cancelled")

        except Exception:
            logger.exception("Voice send flow failed")
            await self._speak("エラーが発生しました")

    async def _record_and_parse(self) -> SendIntent:
        audio = await self._recorder.record_until_silence()
        text = await self._stt.transcribe(audio)
        logger.info("STT result: %s", text)
        return self._intent_parser.parse(text)

    def _resolve_channel(self, intent: SendIntent) -> str | None:
        if intent.channel_name:
            return self._channel_map.get(intent.channel_name)
        return self._active_channel_id or self._default_channel_id

    async def _speak(self, text: str) -> None:
        try:
            audio, sr = await self._tts.synthesize(text)
            await self._player.play(audio, sr)
        except Exception:
            logger.exception("TTS confirmation failed")

    async def _listen_for_confirmation(self) -> ConfirmationResult:
        audio = await self._recorder.record_until_silence()
        text = await self._stt.transcribe(audio)
        text = text.strip()
        logger.info("Confirmation STT: %s", text)

        for word in self._confirm_words:
            if word in text:
                return ConfirmationResult.CONFIRMED

        for word in self._cancel_words:
            if word in text:
                return ConfirmationResult.CANCELLED

        # Default: treat as cancel for safety
        logger.warning("Unrecognized confirmation: %s, treating as cancel", text)
        return ConfirmationResult.CANCELLED
