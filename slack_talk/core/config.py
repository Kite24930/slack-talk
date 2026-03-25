"""SQLite configuration manager."""

from __future__ import annotations

import json
import logging

import aiosqlite

from slack_talk.core.models import AudioSettings, ChannelConfig, DisplaySettings, VoiceSettings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    tts_enabled INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audio_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    speech_rate REAL NOT NULL DEFAULT 1.0,
    volume REAL NOT NULL DEFAULT 0.8,
    queue_ttl_seconds INTEGER NOT NULL DEFAULT 300,
    retry_count INTEGER NOT NULL DEFAULT 2,
    flow_matching_steps INTEGER NOT NULL DEFAULT 10,
    reference_audio_path TEXT
);

CREATE TABLE IF NOT EXISTS voice_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    wakeword TEXT NOT NULL DEFAULT 'OK Slack',
    silence_threshold_seconds REAL NOT NULL DEFAULT 1.5,
    input_device INTEGER,
    output_device INTEGER,
    default_channel_id TEXT
);

CREATE TABLE IF NOT EXISTS display_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    theme TEXT NOT NULL DEFAULT 'dark',
    thread_preview_count INTEGER NOT NULL DEFAULT 2,
    priority_rules TEXT NOT NULL DEFAULT '{}'
);
"""

_SEED = """
INSERT OR IGNORE INTO audio_settings (id) VALUES (1);
INSERT OR IGNORE INTO voice_settings (id) VALUES (1);
INSERT OR IGNORE INTO display_settings (id) VALUES (1);
"""


class ConfigManager:
    def __init__(self, db_path: str = "slack_talk.db") -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.executescript(_SEED)
        await self._db.commit()
        logger.info("ConfigManager initialized: %s", self._db_path)

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None, "ConfigManager not initialized"
        return self._db

    # --- Channels ---

    async def get_all_channels(self) -> list[ChannelConfig]:
        async with self.db.execute("SELECT * FROM channels") as cur:
            rows = await cur.fetchall()
        return [
            ChannelConfig(
                channel_id=r["channel_id"],
                channel_name=r["channel_name"],
                tts_enabled=bool(r["tts_enabled"]),
            )
            for r in rows
        ]

    async def get_enabled_channels(self) -> list[ChannelConfig]:
        async with self.db.execute(
            "SELECT * FROM channels WHERE tts_enabled = 1"
        ) as cur:
            rows = await cur.fetchall()
        return [
            ChannelConfig(
                channel_id=r["channel_id"],
                channel_name=r["channel_name"],
                tts_enabled=True,
            )
            for r in rows
        ]

    async def get_channel(self, channel_id: str) -> ChannelConfig | None:
        async with self.db.execute(
            "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
        ) as cur:
            r = await cur.fetchone()
        if r is None:
            return None
        return ChannelConfig(
            channel_id=r["channel_id"],
            channel_name=r["channel_name"],
            tts_enabled=bool(r["tts_enabled"]),
        )

    async def upsert_channel(self, ch: ChannelConfig) -> None:
        await self.db.execute(
            """INSERT INTO channels (channel_id, channel_name, tts_enabled)
               VALUES (?, ?, ?)
               ON CONFLICT(channel_id)
               DO UPDATE SET channel_name=excluded.channel_name,
                             tts_enabled=excluded.tts_enabled""",
            (ch.channel_id, ch.channel_name, int(ch.tts_enabled)),
        )
        await self.db.commit()

    # --- Audio Settings ---

    async def get_audio_settings(self) -> AudioSettings:
        async with self.db.execute(
            "SELECT * FROM audio_settings WHERE id = 1"
        ) as cur:
            r = await cur.fetchone()
        return AudioSettings(
            speech_rate=r["speech_rate"],
            volume=r["volume"],
            queue_ttl_seconds=r["queue_ttl_seconds"],
            retry_count=r["retry_count"],
            flow_matching_steps=r["flow_matching_steps"],
            reference_audio_path=r["reference_audio_path"],
        )

    async def save_audio_settings(self, s: AudioSettings) -> None:
        await self.db.execute(
            """UPDATE audio_settings SET
               speech_rate=?, volume=?, queue_ttl_seconds=?,
               retry_count=?, flow_matching_steps=?, reference_audio_path=?
               WHERE id = 1""",
            (
                s.speech_rate,
                s.volume,
                s.queue_ttl_seconds,
                s.retry_count,
                s.flow_matching_steps,
                s.reference_audio_path,
            ),
        )
        await self.db.commit()

    # --- Voice Settings ---

    async def get_voice_settings(self) -> VoiceSettings:
        async with self.db.execute(
            "SELECT * FROM voice_settings WHERE id = 1"
        ) as cur:
            r = await cur.fetchone()
        return VoiceSettings(
            wakeword=r["wakeword"],
            silence_threshold_seconds=r["silence_threshold_seconds"],
            input_device=r["input_device"],
            output_device=r["output_device"],
            default_channel_id=r["default_channel_id"],
        )

    async def save_voice_settings(self, s: VoiceSettings) -> None:
        await self.db.execute(
            """UPDATE voice_settings SET
               wakeword=?, silence_threshold_seconds=?,
               input_device=?, output_device=?, default_channel_id=?
               WHERE id = 1""",
            (
                s.wakeword,
                s.silence_threshold_seconds,
                s.input_device,
                s.output_device,
                s.default_channel_id,
            ),
        )
        await self.db.commit()

    # --- Display Settings ---

    async def get_display_settings(self) -> DisplaySettings:
        async with self.db.execute(
            "SELECT * FROM display_settings WHERE id = 1"
        ) as cur:
            r = await cur.fetchone()
        return DisplaySettings(
            theme=r["theme"],
            thread_preview_count=r["thread_preview_count"],
            priority_rules=json.loads(r["priority_rules"]),
        )

    async def save_display_settings(self, s: DisplaySettings) -> None:
        await self.db.execute(
            """UPDATE display_settings SET
               theme=?, thread_preview_count=?, priority_rules=?
               WHERE id = 1""",
            (s.theme, s.thread_preview_count, json.dumps(s.priority_rules)),
        )
        await self.db.commit()
