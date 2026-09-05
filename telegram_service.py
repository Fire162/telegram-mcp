import os
import io
import sys
import json
import time
import fcntl
import asyncio
import datetime
import traceback
from typing import Optional, List, Dict, Any, Union
from telethon import TelegramClient, custom, events
from telethon.tl import functions, types
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

LOCKFILE_PATH = "/tmp/telegram-mcp.lock"


class TelegramService:
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()
        self._lock_fd: Optional[int] = None

    def _acquire_process_lock(self):
        if self._lock_fd is not None:
            return

        fd = os.open(LOCKFILE_PATH, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise RuntimeError(
                "Another telegram-mcp instance is already running and using this session. "
                "Kill the other process first or it will destroy the session. "
                f"Check: ps aux | grep server.py / lsof {LOCKFILE_PATH}"
            )

        os.write(fd, f"pid={os.getpid()}\n".encode())
        os.fsync(fd)
        self._lock_fd = fd

    def _release_process_lock(self):
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None

            try:
                os.unlink(LOCKFILE_PATH)
            except OSError:
                pass

    async def get_client(self) -> TelegramClient:
        async with self._lock:
            if self.client and self.client.is_connected():
                return self.client

            self._acquire_process_lock()

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

    async def _ensure_connected(self) -> TelegramClient:
        try:
            return await self.get_client()
        except (ConnectionError, OSError) as e:
            if "AuthKeyDuplicated" in str(e) or "authorization key" in str(e).lower():
                raise RuntimeError(
                    "Session permanently revoked by Telegram (AuthKeyDuplicatedError). "
                    "This happens when two processes use the same session simultaneously. "
                    "You must re-login: cd /root/bot-mcp && python3 login.py"
                ) from e
            self.client = None
            try:
                return await self.get_client()
            except Exception:
                raise
        except Exception as e:
            err_str = str(e)
            if "AuthKeyDuplicated" in err_str or "authorization key" in err_str.lower():
                raise RuntimeError(
                    "Session permanently revoked by Telegram (AuthKeyDuplicatedError). "
                    "This happens when two processes use the same session simultaneously. "
                    "You must re-login: cd /root/bot-mcp && python3 login.py"
                ) from e
            raise

    async def disconnect(self):
        if self.client and self.client.is_connected():
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self.client = None
        self._release_process_lock()

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
        parse_mode: Optional[str] = "md",
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)

        sent = await client.send_message(
            target,
            text,
            reply_to=reply_to_msg_id,
            parse_mode=parse_mode,
        )
        return self._format_message(sent)

    async def edit_message(
        self,
        bot_username: str,
        message_id: int,
        new_text: str,
        parse_mode: Optional[str] = "md",
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)

        edited = await client.edit_message(
            target,
            message_id,
            new_text,
            parse_mode=parse_mode,
        )
        return self._format_message(edited)

    async def delete_messages(
        self,
        bot_username: str,
        message_ids: List[int],
        revoke: bool = True,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        res = await client.delete_messages(entity, message_ids, revoke=revoke)
        return {
            "success": True,
            "deleted_count": len(res) if isinstance(res, list) else len(message_ids),
            "message_ids": message_ids,
        }

    async def forward_messages(
        self,
        to_chat: str,
        from_chat: str,
        message_ids: List[int],
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target_to = self._clean_bot_username(to_chat)
        target_from = self._clean_bot_username(from_chat)

        forwarded = await client.forward_messages(
            target_to,
            message_ids,
            target_from,
        )
        if not isinstance(forwarded, list):
            forwarded = [forwarded]
        return [self._format_message(m) for m in forwarded]

    async def send_reaction(
        self,
        bot_username: str,
        message_id: int,
        reaction: str,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        emojis = [types.ReactionEmoji(emoticon=reaction)] if reaction else []
        await client(functions.messages.SendReactionRequest(
            peer=entity,
            msg_id=message_id,
            reaction=emojis,
        ))
        return {
            "success": True,
            "message_id": message_id,
            "reaction": reaction or "(cleared)",
        }

    async def send_poll(
        self,
        bot_username: str,
        question: str,
        options: List[str],
        is_quiz: bool = False,
        correct_option_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        import random
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)

        poll = types.Poll(
            id=random.randint(0, 2**63 - 1),
            question=types.TextWithEntities(text=question, entities=[]),
            answers=[
                types.PollAnswer(text=types.TextWithEntities(text=opt, entities=[]), option=bytes([i]))
                for i, opt in enumerate(options)
            ],
            quiz=is_quiz,
        )
        correct_answers = [bytes([correct_option_id])] if is_quiz and correct_option_id is not None else None
        media = types.InputMediaPoll(poll=poll, correct_answers=correct_answers)

        sent = await client.send_message(target, file=media)
        return self._format_message(sent)

    async def mark_chat_read(
        self,
        bot_username: str,
        max_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client.send_read_acknowledge(entity, max_id=max_id)
        return {
            "success": True,
            "chat": target,
            "max_id": max_id,
        }

    async def list_dialogs(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        dialogs = await client.get_dialogs(limit=limit)

        result = []
        for d in dialogs:
            result.append({
                "id": d.id,
                "name": d.name,
                "title": d.title,
                "is_user": d.is_user,
                "is_group": d.is_group,
                "is_channel": d.is_channel,
                "unread_count": d.unread_count,
                "date": d.date.isoformat() if d.date else None,
                "last_message": d.message.text[:100] if (d.message and d.message.text) else None,
            })
        return result

    async def search_messages(
        self,
        bot_username: str,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        messages = await client.get_messages(entity, search=query, limit=limit)
        return [self._format_message(m) for m in messages]

    async def send_file(
        self,
        bot_username: str,
        file_path: str,
        caption: Optional[str] = None,
        reply_to_msg_id: Optional[int] = None,
        voice_note: bool = False,
    ) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)

        sent = await client.send_file(
            target,
            file_path,
            caption=caption,
            reply_to=reply_to_msg_id,
            voice_note=voice_note,
        )
        return self._format_message(sent)

    async def download_media(
        self,
        bot_username: str,
        message_id: int,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
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
        client = await self._ensure_connected()
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
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        msg = None
        if message_id is not None:
            msgs = await client.get_messages(entity, ids=[message_id])
            if msgs and msgs[0]:
                msg = msgs[0]
        else:
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
        client = await self._ensure_connected()
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
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        messages = await client.get_messages(entity, limit=limit)
        return [self._format_message(m) for m in messages]

    async def clear_chat(self, bot_username: str) -> bool:
        client = await self._ensure_connected()
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

    async def execute_code(self, code: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Executes arbitrary Python code asynchronously with live Telethon client and MTProto access.
        """
        client = await self._ensure_connected()

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        lines = code.strip().splitlines()
        indent_code = "\n".join("    " + line for line in lines)
        wrapper = f"""
async def __agent_exec__(client, telegram_service, service, events, functions, types, asyncio, json, os, time):
{indent_code}
"""
        local_ns = {}
        global_ns = {
            "client": client,
            "telegram_service": self,
            "service": self,
            "events": events,
            "functions": functions,
            "types": types,
            "asyncio": asyncio,
            "json": json,
            "os": os,
            "time": time,
        }

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout_capture, stderr_capture

        start_time = time.time()
        try:
            exec(wrapper, global_ns, local_ns)
            fn = local_ns["__agent_exec__"]
            result = await asyncio.wait_for(
                fn(client, self, self, events, functions, types, asyncio, json, os, time),
                timeout=timeout_seconds
            )
            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "return_value": repr(result) if result is not None else None,
                "duration_seconds": round(time.time() - start_time, 3),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "duration_seconds": round(time.time() - start_time, 3),
            }
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

    async def get_bot_info(self, bot_username: str) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)
        full = await client(functions.users.GetFullUserRequest(id=entity))
        user = full.users[0] if full.users else None
        bot_info = getattr(full, "bot_info", None) or getattr(full.full_user, "bot_info", None)

        commands = []
        if bot_info and hasattr(bot_info, "commands") and bot_info.commands:
            commands = [{"command": c.command, "description": c.description} for c in bot_info.commands]

        first_name = getattr(user, "first_name", "") or ""
        last_name = getattr(user, "last_name", "") or ""
        name = f"{first_name} {last_name}".strip() or first_name

        return {
            "id": getattr(user, "id", None),
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "username": getattr(user, "username", None),
            "is_bot": getattr(user, "bot", True),
            "about": getattr(full.full_user, "about", None),
            "commands": commands,
        }

    async def pin_message(
        self,
        bot_username: str,
        message_id: int,
        notify: bool = False,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client.pin_message(entity, message_id, notify=notify)
        return {"success": True, "pinned_message_id": message_id}

    async def unpin_message(
        self,
        bot_username: str,
        message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client.unpin_message(entity, message_id)
        return {"success": True, "unpinned_message_id": message_id or "all"}

    async def get_message_context(
        self,
        bot_username: str,
        message_id: int,
        limit_before: int = 5,
        limit_after: int = 5,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        min_id = max(0, message_id - limit_before - 1)
        max_id = message_id + limit_after + 1
        messages = await client.get_messages(entity, min_id=min_id, max_id=max_id)
        return {
            "target_message_id": message_id,
            "count": len(messages),
            "messages": [self._format_message(m) for m in messages],
        }

    async def send_album(
        self,
        bot_username: str,
        file_paths: List[str],
        caption: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)

        for p in file_paths:
            if not os.path.exists(p):
                raise FileNotFoundError(f"File not found: {p}")

        sent = await client.send_file(target, file_paths, caption=caption)
        if not isinstance(sent, list):
            sent = [sent]
        return [self._format_message(m) for m in sent]

    async def save_draft(
        self,
        bot_username: str,
        text: str,
        reply_to_msg_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        reply_to_obj = types.InputReplyToMessage(reply_to_msg_id=reply_to_msg_id) if reply_to_msg_id else None

        res = await client(
            functions.messages.SaveDraftRequest(
                peer=entity,
                message=text,
                reply_to=reply_to_obj,
                no_webpage=True,
            )
        )
        return {"success": bool(res), "target": target, "draft_text": text}

    async def schedule_message(
        self,
        bot_username: str,
        text: str,
        schedule_in_seconds: Optional[int] = None,
        schedule_date_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        if schedule_in_seconds is not None:
            schedule_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=schedule_in_seconds)
        elif schedule_date_iso is not None:
            schedule_date = datetime.datetime.fromisoformat(schedule_date_iso)
            if schedule_date.tzinfo is None:
                schedule_date = schedule_date.replace(tzinfo=datetime.timezone.utc)
        else:
            raise ValueError("Must provide either schedule_in_seconds or schedule_date_iso")

        sent = await client.send_message(entity, text, schedule=schedule_date)
        return {
            "success": True,
            "scheduled_message_id": sent.id,
            "scheduled_date": sent.date.isoformat() if sent.date else schedule_date.isoformat(),
            "text": text,
        }

    async def get_scheduled_messages(self, bot_username: str) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        sched = await client(functions.messages.GetScheduledHistoryRequest(peer=entity, hash=0))
        return [self._format_message(m) for m in sched.messages]

    async def delete_scheduled_messages(
        self,
        bot_username: str,
        message_ids: List[int],
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client(functions.messages.DeleteScheduledMessagesRequest(peer=entity, id=message_ids))
        return {"success": True, "deleted_ids": message_ids}

    async def get_pinned_messages(
        self,
        bot_username: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        messages = await client.get_messages(entity, filter=types.InputMessagesFilterPinned(), limit=limit)
        return [self._format_message(m) for m in messages]

    async def mute_chat(
        self,
        bot_username: str,
        duration_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        if duration_seconds is not None and duration_seconds > 0:
            mute_until = int(time.time()) + duration_seconds
        else:
            mute_until = 2147483647  # Permanently

        await client(
            functions.account.UpdateNotifySettingsRequest(
                peer=types.InputNotifyPeer(entity),
                settings=types.InputPeerNotifySettings(mute_until=mute_until),
            )
        )
        return {"success": True, "target": target, "muted_until_unix": mute_until}

    async def unmute_chat(self, bot_username: str) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        await client(
            functions.account.UpdateNotifySettingsRequest(
                peer=types.InputNotifyPeer(entity),
                settings=types.InputPeerNotifySettings(mute_until=0),
            )
        )
        return {"success": True, "target": target, "muted": False}

    async def export_chat(
        self,
        bot_username: str,
        limit: int = 50,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        raw_messages = await client.get_messages(entity, limit=limit)
        formatted = [self._format_message(m) for m in reversed(raw_messages)]

        if format.lower() == "markdown":
            lines = [f"# Chat Transcript: {target}", f"**Total Messages:** {len(formatted)}\n"]
            for m in formatted:
                sender = m.get("sender", "unknown")
                date = m.get("date", "")
                text = m.get("text") or "[no text]"
                media = f" *(media: {m['media_type']})*" if m.get("media_type") else ""
                lines.append(f"- **[{date}] {sender}{media}:** {text}")
            content = "\n".join(lines)
            return {"format": "markdown", "count": len(formatted), "content": content}
        else:
            return {"format": "json", "count": len(formatted), "messages": formatted}

    async def get_chat_members(
        self,
        bot_username: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        participants = await client.get_participants(entity, limit=limit)
        result = []
        for p in participants:
            first_name = getattr(p, "first_name", "") or ""
            last_name = getattr(p, "last_name", "") or ""
            name = f"{first_name} {last_name}".strip() or first_name
            result.append({
                "id": p.id,
                "name": name,
                "first_name": first_name,
                "last_name": last_name,
                "username": getattr(p, "username", None),
                "is_bot": getattr(p, "bot", False),
            })
        return result

    async def get_contacts(
        self,
        query: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        client = await self._ensure_connected()
        contacts_res = await client(functions.contacts.GetContactsRequest(hash=0))
        users = contacts_res.users if hasattr(contacts_res, "users") else []

        result = []
        query_lower = query.lower() if query else None
        for u in users:
            first_name = getattr(u, "first_name", "") or ""
            last_name = getattr(u, "last_name", "") or ""
            name = f"{first_name} {last_name}".strip() or first_name
            username = getattr(u, "username", "") or ""
            phone = getattr(u, "phone", "") or ""

            if query_lower:
                if (
                    query_lower not in name.lower()
                    and query_lower not in username.lower()
                    and query_lower not in phone
                ):
                    continue

            masked_phone = None
            if phone:
                masked_phone = f"+{phone[:2]} ****** {phone[-4:]}" if len(phone) >= 6 else "***"

            result.append({
                "id": u.id,
                "name": name,
                "first_name": first_name,
                "last_name": last_name,
                "username": username or None,
                "phone": masked_phone,
                "is_bot": getattr(u, "bot", False),
            })
            if len(result) >= limit:
                break
        return result

    async def resolve_peer(self, peer: str) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = peer.strip()
        if target.isdigit():
            target = int(target)

        entity = await client.get_entity(target)
        first_name = getattr(entity, "first_name", "") or ""
        last_name = getattr(entity, "last_name", "") or ""
        title = getattr(entity, "title", "") or ""
        name = title or f"{first_name} {last_name}".strip() or first_name

        entity_type = "user"
        if getattr(entity, "bot", False):
            entity_type = "bot"
        elif getattr(entity, "megagroup", False) or getattr(entity, "gigagroup", False):
            entity_type = "supergroup"
        elif getattr(entity, "broadcast", False):
            entity_type = "channel"
        elif getattr(entity, "is_group", False):
            entity_type = "group"

        return {
            "id": entity.id,
            "type": entity_type,
            "name": name,
            "username": getattr(entity, "username", None),
            "verified": getattr(entity, "verified", False),
            "restricted": getattr(entity, "restricted", False),
            "scam": getattr(entity, "scam", False),
            "fake": getattr(entity, "fake", False),
        }

    async def wait_for(
        self,
        bot_username: str,
        text_contains: Optional[str] = None,
        after_message_id: Optional[int] = None,
        target_message_id: Optional[int] = None,
        wait_for_edit: bool = False,
        timeout_seconds: int = 30,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        client = await self._ensure_connected()
        target = self._clean_bot_username(bot_username)
        entity = await client.get_input_entity(target)

        start_time = asyncio.get_event_loop().time()
        initial_text = None
        initial_edit_date = None

        if target_message_id is not None:
            init_msgs = await client.get_messages(entity, ids=[target_message_id])
            if init_msgs and init_msgs[0]:
                initial_text = init_msgs[0].text
                initial_edit_date = init_msgs[0].edit_date

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            if target_message_id is not None or wait_for_edit:
                check_id = target_message_id
                if check_id is None:
                    recent = await client.get_messages(entity, limit=1)
                    if recent:
                        check_id = recent[0].id

                if check_id is not None:
                    msgs = await client.get_messages(entity, ids=[check_id])
                    if msgs and msgs[0]:
                        cur = msgs[0]
                        has_changed = (cur.text != initial_text) or (
                            cur.edit_date != initial_edit_date and cur.edit_date is not None
                        )
                        text_matches = not text_contains or (text_contains.lower() in (cur.text or "").lower())
                        if has_changed and text_matches:
                            return {
                                "status": "success",
                                "matched_event": "message_edited",
                                "message": self._format_message(cur),
                            }
            else:
                messages = await client.get_messages(entity, limit=10)
                for msg in messages:
                    if not msg.out and (after_message_id is None or msg.id > after_message_id):
                        if not text_contains or (text_contains.lower() in (msg.text or "").lower()):
                            return {
                                "status": "success",
                                "matched_event": "new_message",
                                "message": self._format_message(msg),
                            }

            await asyncio.sleep(poll_interval)

        return {
            "status": "timeout",
            "matched": False,
            "message": f"Timed out after {timeout_seconds}s waiting for matching message from {target}",
        }


telegram_service = TelegramService()

