"""Tests for Slack message text preprocessor."""

from slack_talk.slack.preprocessor import preprocess


class TestMentions:
    def test_user_mention_replaced(self):
        users = {"U123": "Taro"}
        result = preprocess("<@U123> hello", users=users, channels={})
        assert result == "Taro hello"

    def test_unknown_user_mention(self):
        result = preprocess("<@UUNKNOWN> hello", users={}, channels={})
        assert result == "誰か hello"


class TestChannelLinks:
    def test_channel_link_replaced(self):
        channels = {"C123": "general"}
        result = preprocess("<#C123> を確認", users={}, channels=channels)
        assert result == "general を確認"

    def test_unknown_channel_link(self):
        result = preprocess("<#CUNKNOWN> を確認", users={}, channels={})
        assert result == "チャンネル を確認"


class TestUrls:
    def test_url_replaced(self):
        result = preprocess("see <https://example.com>", users={}, channels={})
        assert result == "see リンク"

    def test_url_with_label(self):
        result = preprocess("see <https://example.com|Example>", users={}, channels={})
        assert result == "see Example"


class TestCodeBlocks:
    def test_code_block_replaced(self):
        result = preprocess("before ```code here``` after", users={}, channels={})
        assert result == "before コードブロック省略 after"

    def test_inline_code_kept(self):
        result = preprocess("use `variable` here", users={}, channels={})
        assert result == "use variable here"


class TestMarkup:
    def test_bold_stripped(self):
        result = preprocess("this is *bold* text", users={}, channels={})
        assert result == "this is bold text"

    def test_italic_stripped(self):
        result = preprocess("this is _italic_ text", users={}, channels={})
        assert result == "this is italic text"

    def test_strikethrough_stripped(self):
        result = preprocess("this is ~deleted~ text", users={}, channels={})
        assert result == "this is deleted text"


class TestEmoji:
    def test_known_emoji(self):
        result = preprocess("good :thumbsup:", users={}, channels={})
        assert result == "good サムズアップ"

    def test_unknown_emoji_removed(self):
        result = preprocess("test :custom_emoji:", users={}, channels={})
        assert result == "test"
