import os
import json
import asyncio
import time
from typing import Optional, List, Dict, Any, Union
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
        return target if (target.startswith("@") or target.startswith("-") or target.isdigit()) else f"@{target}"

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

        media_type = None
        media_info = None
        if msg.photo:
            media_type = "photo"
        elif msg.document:
            media_type = "document"
            media_info = {
                "mime_type": msg.file.mime_type if msg.file else None,
                "size_bytes": msg.file.size if msg.file else None,
                "name": msg.file.name if msg.file else None,
            }
        elif msg.voice:
            media_type = "voice"
        elif msg.audio:
            media_type = "audio"

        return {
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "sender": "user" if msg.out else "bot",
            "text": msg.text or "",
            "media_type": media_type,
            "media_info": media_info,
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

    async def send_file(
        self,
        bot_username: str,
        file_path: str,
        caption: Optional[str] = None,
        reply_to_msg_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        client = await self.get_client()
        target = self._clean_bot_username(bot_username)

        sent = await client.send_file(
            target,
            file_path,
            caption=caption,
            reply_to=reply_to_msg_id,
        )
        return self._format_message(sent)

    async def download_media(
        self,
        bot_username: str,
        message_id: int,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        msgs = await client.get_messages(entity, ids=[message_id])
        if not msgs or msgs[0] is None:
            raise ValueError(f"Message ID {message_id} was not found.")

        msg = msgs[0]
        if not msg.media:
            raise ValueError(f"Message ID {message_id} does not contain any media.")

        save_dir = output_dir or os.path.join(os.getcwd(), "downloads")
        os.makedirs(save_dir, exist_ok=True)

        downloaded_path = await msg.download_media(file=save_dir)
        file_size = os.path.getsize(downloaded_path) if downloaded_path and os.path.exists(downloaded_path) else 0

        return {
            "success": True,
            "file_path": downloaded_path,
            "file_name": os.path.basename(downloaded_path) if downloaded_path else None,
            "size_bytes": file_size,
        }

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
        message_id: Optional[int] = None,
        button_text: Optional[str] = None,
        button_index: Optional[int] = None,
        wait_update: bool = True,
    ) -> Dict[str, Any]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        msg = None
        if message_id is not None:
            msgs = await client.get_messages(entity, ids=[message_id])
            if msgs and msgs[0]:
                msg = msgs[0]
        else:
            # Get latest message from bot with buttons
            messages = await client.get_messages(entity, limit=5)
            for m in messages:
                if m.buttons:
                    msg = m
                    break

        if not msg:
            raise ValueError(f"No message with buttons found (target ID: {message_id}).")

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
            fresh = await client.get_messages(entity, ids=[msg.id])
            if fresh and fresh[0]:
                updated_message = self._format_message(fresh[0])

        popup_text = None
        if hasattr(click_result, "message") and click_result.message:
            popup_text = click_result.message

        return {
            "success": True,
            "message_id": msg.id,
            "popup_alert": popup_text,
            "updated_message": updated_message,
        }

    async def inline_query(
        self,
        bot_username: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        client = await self.get_client()
        target = self._clean_bot_username(bot_username)

        results = await client.inline_query(target, query)
        formatted_results = []
        for res in results:
            formatted_results.append({
                "id": str(res.id),
                "title": getattr(res, "title", None),
                "description": getattr(res, "description", None),
                "type": getattr(res, "type", None),
                "url": getattr(res, "url", None),
                "send_message_text": getattr(getattr(res, "send_message", None), "message", None),
            })
        return formatted_results

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

    async def run_test_suite(
        self,
        bot_username: str,
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        start_time = time.time()
        results = []
        last_sent_id = None
        last_reply_id = None
        suite_passed = True

        for idx, step in enumerate(steps, 1):
            action = step.get("action", "").lower()
            step_result = {"step": idx, "action": action, "passed": True}

            try:
                if action in ("send", "send_command"):
                    text = step.get("text") or step.get("command", "")
                    reply_to = step.get("reply_to_msg_id")
                    sent = await self.send_message(bot_username, text, reply_to_msg_id=reply_to)
                    last_sent_id = sent["id"]
                    step_result["sent"] = sent

                elif action == "send_file":
                    file_path = step.get("file_path", "")
                    caption = step.get("caption")
                    sent = await self.send_file(bot_username, file_path, caption=caption)
                    last_sent_id = sent["id"]
                    step_result["sent"] = sent

                elif action == "sleep":
                    seconds = float(step.get("seconds", 1.0))
                    await asyncio.sleep(seconds)
                    step_result["slept_seconds"] = seconds

                elif action in ("wait_reply", "get_reply"):
                    timeout = int(step.get("timeout_seconds", 10))
                    reply = await self.wait_for_reply(bot_username, after_message_id=last_sent_id, timeout_seconds=timeout)
                    if not reply:
                        step_result["passed"] = False
                        step_result["error"] = "Timeout waiting for bot reply."
                        suite_passed = False
                    else:
                        last_reply_id = reply["id"]
                        step_result["reply"] = reply

                elif action == "assert_reply":
                    expected = step.get("contains", "")
                    timeout = int(step.get("timeout_seconds", 10))
                    reply = await self.wait_for_reply(bot_username, after_message_id=last_sent_id, timeout_seconds=timeout)
                    if not reply:
                        step_result["passed"] = False
                        step_result["error"] = f"Timeout waiting for reply to assert '{expected}'."
                        suite_passed = False
                    else:
                        last_reply_id = reply["id"]
                        received_text = reply.get("text", "")
                        if expected.lower() not in received_text.lower():
                            step_result["passed"] = False
                            step_result["error"] = f"Assertion failed: expected '{expected}' in '{received_text}'"
                            suite_passed = False
                        step_result["reply"] = reply

                elif action == "click_button":
                    msg_id = step.get("message_id") or last_reply_id
                    btn_text = step.get("text") or step.get("button_text")
                    btn_idx = step.get("index") or step.get("button_index")
                    wait_up = step.get("wait_update", True)
                    click_res = await self.click_inline_button(
                        bot_username,
                        message_id=msg_id,
                        button_text=btn_text,
                        button_index=btn_idx,
                        wait_update=wait_up,
                    )
                    step_result["click_result"] = click_res

                elif action == "clear_chat":
                    await self.clear_chat(bot_username)
                    step_result["cleared"] = True

                else:
                    step_result["passed"] = False
                    step_result["error"] = f"Unknown action: '{action}'"
                    suite_passed = False

            except Exception as e:
                step_result["passed"] = False
                step_result["error"] = str(e)
                suite_passed = False

            results.append(step_result)
            if not step_result["passed"] and step.get("stop_on_failure", True):
                break

        return {
            "suite_passed": suite_passed,
            "total_steps": len(steps),
            "executed_steps": len(results),
            "duration_seconds": round(time.time() - start_time, 2),
            "steps_results": results,
        }


telegram_service = TelegramService()
