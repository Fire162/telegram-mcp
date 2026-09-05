import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from telegram_service import TelegramService


class TestTelegramService(unittest.TestCase):
    def setUp(self):
        self.service = TelegramService()

    def test_clean_bot_username(self):
        self.assertEqual(self.service._clean_bot_username("@test_bot"), "@test_bot")
        self.assertEqual(self.service._clean_bot_username("test_bot"), "@test_bot")
        self.assertEqual(self.service._clean_bot_username("https://t.me/test_bot"), "@test_bot")
        self.assertEqual(self.service._clean_bot_username("t.me/test_bot"), "@test_bot")
        self.assertEqual(self.service._clean_bot_username("12345678"), "12345678")

    def test_format_message_text(self):
        mock_msg = MagicMock()
        mock_msg.id = 42
        mock_msg.date.isoformat.return_value = "2026-09-05T12:00:00+00:00"
        mock_msg.out = False
        mock_msg.text = "Hello from bot"
        mock_msg.photo = None
        mock_msg.document = None
        mock_msg.voice = None
        mock_msg.audio = None
        mock_msg.buttons = None

        formatted = self.service._format_message(mock_msg)
        self.assertEqual(formatted["id"], 42)
        self.assertEqual(formatted["sender"], "bot")
        self.assertEqual(formatted["text"], "Hello from bot")
        self.assertIsNone(formatted["media_type"])
        self.assertIsNone(formatted["buttons"])

    def test_format_message_outgoing(self):
        mock_msg = MagicMock()
        mock_msg.id = 43
        mock_msg.date.isoformat.return_value = "2026-09-05T12:01:00+00:00"
        mock_msg.out = True
        mock_msg.text = "/start"
        mock_msg.photo = None
        mock_msg.document = None
        mock_msg.voice = None
        mock_msg.audio = None
        mock_msg.buttons = None

        formatted = self.service._format_message(mock_msg)
        self.assertEqual(formatted["id"], 43)
        self.assertEqual(formatted["sender"], "user")
        self.assertEqual(formatted["text"], "/start")

    def test_format_message_buttons(self):
        btn1 = MagicMock()
        btn1.text = "Option 1"
        btn1.data = b"opt_1"
        btn2 = MagicMock()
        btn2.text = "Option 2"
        btn2.data = None

        mock_msg = MagicMock()
        mock_msg.id = 44
        mock_msg.date.isoformat.return_value = "2026-09-05T12:02:00+00:00"
        mock_msg.out = False
        mock_msg.text = "Choose option:"
        mock_msg.photo = None
        mock_msg.document = None
        mock_msg.voice = None
        mock_msg.audio = None
        mock_msg.buttons = [[btn1, btn2]]

        formatted = self.service._format_message(mock_msg)
        self.assertIsNotNone(formatted["buttons"])
        self.assertEqual(len(formatted["buttons"]), 1)
        self.assertEqual(len(formatted["buttons"][0]), 2)
        self.assertEqual(formatted["buttons"][0][0]["text"], "Option 1")
        self.assertEqual(formatted["buttons"][0][0]["data"], "opt_1")

    def test_wait_for_timeout(self):
        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="target_entity")
        mock_client.get_messages = AsyncMock(return_value=[])

        with patch.object(self.service, "_ensure_connected", return_value=mock_client):
            res = asyncio.run(
                self.service.wait_for(
                    bot_username="@test_bot",
                    text_contains="some_string",
                    timeout_seconds=1,
                    poll_interval=0.2,
                )
            )
            self.assertEqual(res["status"], "timeout")
            self.assertFalse(res["matched"])

    def test_get_web_app_url_main_app(self):
        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="target_entity")
        mock_client.get_messages = AsyncMock(return_value=[])
        mock_main_res = MagicMock()
        mock_main_res.url = "https://twebappcontent.stel.com/testbot#tgWebAppData=123"
        mock_client.side_effect = lambda req: mock_main_res

        with patch.object(self.service, "_ensure_connected", return_value=mock_client):
            res = asyncio.run(self.service.get_web_app_url("testbot"))
            self.assertEqual(res["app_type"], "main_app")
            self.assertEqual(res["web_app_url"], "https://twebappcontent.stel.com/testbot#tgWebAppData=123")
            self.assertEqual(res["bot_username"], "@testbot")

    def test_get_web_app_url_inline_button(self):
        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="target_entity")
        btn = MagicMock()
        btn.text = "Open Game"
        btn.url = None
        btn_raw = MagicMock()
        btn_raw.web_app = MagicMock()
        btn_raw.web_app.url = "https://example.com/app"
        btn.button = btn_raw

        mock_msg = MagicMock()
        mock_msg.id = 101
        mock_msg.buttons = [[btn]]
        mock_client.get_messages = AsyncMock(return_value=[mock_msg])

        mock_res = MagicMock()
        mock_res.url = "https://example.com/app#tgWebAppData=xyz"
        mock_client.side_effect = lambda req: mock_res

        with patch.object(self.service, "_ensure_connected", return_value=mock_client):
            res = asyncio.run(self.service.get_web_app_url("testbot", button_text="Open Game"))
            self.assertEqual(res["app_type"], "inline_button")
            self.assertEqual(res["web_app_url"], "https://example.com/app#tgWebAppData=xyz")
            self.assertEqual(res["button_text"], "Open Game")
            self.assertEqual(res["message_id"], 101)


if __name__ == "__main__":
    unittest.main()
