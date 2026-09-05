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
        self.assertEqual(self.service._clean_bot_username("12345678"), 12345678)
        self.assertEqual(self.service._clean_bot_username("-10012345678"), -10012345678)
        self.assertEqual(self.service._clean_bot_username(12345678), 12345678)

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
    def test_send_poll(self):
        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="target_entity")
        mock_sent = MagicMock()
        mock_sent.id = 55
        mock_sent.date.isoformat.return_value = "2026-09-05T12:00:00+00:00"
        mock_sent.out = True
        mock_sent.text = "Favorite color?"
        mock_sent.photo = None
        mock_sent.document = None
        mock_sent.voice = None
        mock_sent.audio = None
        mock_sent.buttons = None
        mock_client.send_message = AsyncMock(return_value=mock_sent)

        with patch.object(self.service, "_ensure_connected", return_value=mock_client):
            res = asyncio.run(
                self.service.send_poll(
                    bot_username="@test_bot",
                    question="Favorite color?",
                    options=["Red", "Blue"],
                )
            )
            self.assertEqual(res["id"], 55)
            self.assertEqual(res["text"], "Favorite color?")


if __name__ == "__main__":
    unittest.main()
