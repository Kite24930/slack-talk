"""Intent parser for voice commands."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SendIntent:
    """Parsed intent representing a message to send to a Slack channel."""

    channel_name: str | None  # None = use active/default channel
    message: str


class IntentParser:
    """Parse voice command text into structured SendIntent.

    Supports patterns like:
    - "{channel}に{message}" / "{channel}へ{message}"
    - "{channel}に送って、{message}"
    - "{message}を{channel}に送って"
    """

    def __init__(self, known_channels: set[str] | None = None) -> None:
        self._known_channels = known_channels or set()
        self._build_patterns()

    def _build_patterns(self) -> None:
        """Build regex patterns from known channel names."""
        if self._known_channels:
            escaped = [
                re.escape(ch)
                for ch in sorted(self._known_channels, key=len, reverse=True)
            ]
            ch_pattern = "|".join(escaped)
        else:
            ch_pattern = r"\S+"

        self._patterns = [
            # "{ch}に送って、{message}" / "{ch}に送って{message}"
            re.compile(
                rf"(?P<channel>{ch_pattern})[にへ]送って[、,\s]*(?P<message>.+)",
                re.DOTALL,
            ),
            # "{message}を{ch}に送って"
            re.compile(
                rf"(?P<message>.+?)を(?P<channel>{ch_pattern})[にへ]送って",
                re.DOTALL,
            ),
            # "{ch}に{message}" / "{ch}へ{message}"
            re.compile(
                rf"(?P<channel>{ch_pattern})[にへ](?P<message>.+)",
                re.DOTALL,
            ),
        ]

    def update_channels(self, channels: set[str]) -> None:
        """Update known channel list and rebuild patterns."""
        self._known_channels = channels
        self._build_patterns()

    def parse(self, text: str) -> SendIntent:
        """Parse text into a SendIntent."""
        text = text.strip()

        for pattern in self._patterns:
            m = pattern.match(text)
            if m:
                channel = m.group("channel").strip()
                message = m.group("message").strip()
                if channel in self._known_channels:
                    return SendIntent(channel_name=channel, message=message)

        # No channel found → default
        return SendIntent(channel_name=None, message=text)
