import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from telethon import TelegramClient, custom
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()


class TelegramService:
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> TelegramClient:
        async with self._lock:
            if self.client and self.client.is_connected():
                return self.client

            api_id_str = os.environ.get("TELEGRAM_API_ID")
            api_hash = os.environ.get("TELEGRAM_API_HASH")
            session_str = os.environ.get("TELEGRAM_SESSION", "")
            is_test_mode = os.environ.get("TELEGRAM_TEST_MODE", "false").lower() == "true"

            if not api_id_str or not api_hash:
                raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured in .env.")

            api_id = int(api_id_str)
            session = StringSession(session_str)
            self.client = TelegramClient(session, api_id, api_hash)

            if is_test_mode:
                self.client.session.set_dc(2, "149.154.167.40", 443)

            await self.client.connect()
            if not await self.client.is_user_authorized():
                raise PermissionError(
                    "Telegram client is not authorized. Please run 'python3 login.py' to authenticate first."
                )

            return self.client

    def _clean_bot_username(self, username: str) -> str:
        target = username or os.environ.get("DEFAULT_TARGET_BOT", "")
        if not target:
            raise ValueError("Bot username was not provided and DEFAULT_TARGET_BOT is not configured.")
        return target if target.startswith("@") else f"@{target}"

    def _format_message(self, msg: custom.Message) -> Dict[str, Any]:
        buttons = []
        if msg.buttons:
            for row in msg.buttons:
                row_buttons = []
                for btn in row:
                    data_str = None
                    if hasattr(btn, "data") and btn.data:
                        try:
                            data_str = btn.data.decode("utf-8")
                        except Exception:
                            data_str = str(btn.data)
                    row_buttons.append({
                        "text": btn.text,
                        "data": data_str,
                        "url": getattr(btn, "url", None),
                    })
                if row_buttons:
                    buttons.append(row_buttons)

        return {
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "sender": "user" if msg.out else "bot",
            "text": msg.text or "",
            "buttons": buttons if buttons else None,
        }

    async def send_message(
        self,
        bot_username: str,
        text: str,
        reply_to_msg_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)

        sent = await client.send_message(
            target,
            text,
            reply_to=reply_to_msg_id,
        )
        return self._format_message(sent)

    async def wait_for_reply(
        self,
        bot_username: str,
        after_message_id: Optional[int] = None,
        timeout_seconds: int = 10,
    ) -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            messages = await client.get_messages(entity, limit=5)
            for msg in messages:
                if not msg.out and (after_message_id is None or msg.id > after_message_id):
                    return self._format_message(msg)
            await asyncio.sleep(0.8)

        return None

    async def click_inline_button(
        self,
        bot_username: str,
        message_id: int,
        button_text: Optional[str] = None,
        button_index: Optional[int] = None,
        wait_update: bool = True,
    ) -> Dict[str, Any]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        msgs = await client.get_messages(entity, ids=[message_id])
        if not msgs or msgs[0] is None:
            raise ValueError(f"Message with ID {message_id} was not found.")

        msg = msgs[0]
        if not msg.buttons:
            raise ValueError(f"Message ID {message_id} has no buttons.")

        click_result = None
        if button_text:
            click_result = await msg.click(text=button_text)
        elif button_index is not None:
            click_result = await msg.click(button_index)
        else:
            click_result = await msg.click(0)

        updated_message = None
        if wait_update:
            await asyncio.sleep(1.0)
            fresh = await client.get_messages(entity, ids=[message_id])
            if fresh and fresh[0]:
                updated_message = self._format_message(fresh[0])

        popup_text = None
        if hasattr(click_result, "message") and click_result.message:
            popup_text = click_result.message

        return {
            "success": True,
            "popup_alert": popup_text,
            "updated_message": updated_message,
        }

    async def get_chat_history(
        self,
        bot_username: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        messages = await client.get_messages(entity, limit=limit)
        return [self._format_message(m) for m in messages]

    async def clear_chat(self, bot_username: str) -> bool:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client.delete_dialog(entity)
        return True


telegram_service = TelegramService()
