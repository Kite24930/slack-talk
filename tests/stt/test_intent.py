"""Tests for intent parser."""

from slack_talk.stt.intent import IntentParser, SendIntent


class TestIntentParser:
    def setup_method(self):
        self.parser = IntentParser(
            known_channels={"general", "random", "dev", "お知らせ"}
        )

    def test_channel_ni_message(self):
        result = self.parser.parse("generalにお疲れ様です")
        assert isinstance(result, SendIntent)
        assert result.channel_name == "general"
        assert result.message == "お疲れ様です"

    def test_channel_he_message(self):
        result = self.parser.parse("randomへ今日のランチどうする")
        assert isinstance(result, SendIntent)
        assert result.channel_name == "random"
        assert result.message == "今日のランチどうする"

    def test_channel_ni_okutte_message(self):
        result = self.parser.parse("devに送って、ビルド通りました")
        assert isinstance(result, SendIntent)
        assert result.channel_name == "dev"
        assert result.message == "ビルド通りました"

    def test_reverse_order(self):
        result = self.parser.parse("了解ですをgeneralに送って")
        assert isinstance(result, SendIntent)
        assert result.channel_name == "general"
        assert result.message == "了解です"

    def test_no_channel_uses_default(self):
        result = self.parser.parse("お疲れ様です")
        assert isinstance(result, SendIntent)
        assert result.channel_name is None
        assert result.message == "お疲れ様です"

    def test_japanese_channel_name(self):
        result = self.parser.parse("お知らせに明日は休みです")
        assert isinstance(result, SendIntent)
        assert result.channel_name == "お知らせ"
        assert result.message == "明日は休みです"
