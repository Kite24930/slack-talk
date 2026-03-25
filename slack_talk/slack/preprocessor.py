"""Slack message text preprocessor for TTS."""

from __future__ import annotations

import re

# Known emoji -> Japanese reading
_EMOJI_MAP: dict[str, str] = {
    "thumbsup": "サムズアップ",
    "thumbsdown": "サムズダウン",
    "heart": "ハート",
    "smile": "スマイル",
    "laughing": "笑い",
    "cry": "泣き",
    "fire": "ファイヤー",
    "tada": "おめでとう",
    "wave": "手を振る",
    "clap": "拍手",
    "eyes": "目",
    "rocket": "ロケット",
    "white_check_mark": "チェック",
    "x": "バツ",
    "warning": "警告",
    "bulb": "ひらめき",
    "memo": "メモ",
    "pray": "お願い",
    "muscle": "力こぶ",
    "100": "百点",
}


def preprocess(
    text: str,
    *,
    users: dict[str, str],
    channels: dict[str, str],
) -> str:
    """Transform Slack mrkdwn text into TTS-friendly plain text."""
    # Code blocks first (before other transforms)
    text = re.sub(r"```[\s\S]*?```", "コードブロック省略", text)
    # Inline code: strip backticks
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # User mentions
    def _replace_user(m: re.Match) -> str:
        uid = m.group(1)
        return users.get(uid, "誰か")

    text = re.sub(r"<@(\w+)>", _replace_user, text)

    # Channel links
    def _replace_channel(m: re.Match) -> str:
        cid = m.group(1)
        return channels.get(cid, "チャンネル")

    text = re.sub(r"<#(\w+)(?:\|[^>]*)?>", _replace_channel, text)

    # URLs with labels
    text = re.sub(r"<https?://[^|>]+\|([^>]+)>", r"\1", text)
    # URLs without labels
    text = re.sub(r"<https?://[^>]+>", "リンク", text)

    # Markup
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    text = re.sub(r"(?<!\w)~([^~]+)~(?!\w)", r"\1", text)

    # Emoji
    def _replace_emoji(m: re.Match) -> str:
        name = m.group(1)
        return _EMOJI_MAP.get(name, "")

    text = re.sub(r":(\w+):", _replace_emoji, text)

    # Clean up extra whitespace
    text = re.sub(r"  +", " ", text).strip()

    return text
