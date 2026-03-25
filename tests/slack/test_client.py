"""Tests for Slack client message parsing."""

from slack_talk.slack.client import SlackListener


class TestParseMessageEvent:
    def test_parse_normal_message(self):
        event = {
            "type": "message",
            "channel": "C123",
            "user": "U456",
            "text": "Hello world",
            "ts": "1234567890.123456",
        }
        users = {"U456": "Taro"}
        channels = {"C123": "general"}
        msg = SlackListener.parse_message_event(event, users, channels)
        assert msg is not None
        assert msg.channel_id == "C123"
        assert msg.channel_name == "general"
        assert msg.user_name == "Taro"
        assert msg.text == "Hello world"
        assert msg.is_thread_reply is False

    def test_parse_thread_reply(self):
        event = {
            "type": "message",
            "channel": "C123",
            "user": "U456",
            "text": "Reply",
            "ts": "1234567890.123457",
            "thread_ts": "1234567890.123456",
        }
        users = {"U456": "Taro"}
        channels = {"C123": "general"}
        msg = SlackListener.parse_message_event(event, users, channels)
        assert msg is not None
        assert msg.is_thread_reply is True
        assert msg.thread_ts == "1234567890.123456"

    def test_ignore_bot_message(self):
        event = {
            "type": "message",
            "subtype": "bot_message",
            "channel": "C123",
            "text": "Bot says",
            "ts": "1234567890.123456",
        }
        msg = SlackListener.parse_message_event(event, {}, {})
        assert msg is None

    def test_ignore_message_changed(self):
        event = {
            "type": "message",
            "subtype": "message_changed",
            "channel": "C123",
            "ts": "1234567890.123456",
        }
        msg = SlackListener.parse_message_event(event, {}, {})
        assert msg is None
