#!/usr/bin/env python3
import json
import signal
import sys
import asyncio
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer
from telegram_service import telegram_service


@asynccontextmanager
async def lifespan(server):
    try:
        await telegram_service.get_client()
    except Exception as e:
        print(f"[telegram-mcp] Startup warning: {e}", file=sys.stderr)
        print("[telegram-mcp] Server is running but Telegram is not connected.", file=sys.stderr)
        print("[telegram-mcp] Use the telegram_status tool to check or run: python3 /root/bot-mcp/login.py", file=sys.stderr)
    try:
        yield {}
    finally:
        await telegram_service.disconnect()


MCP_INSTRUCTIONS = """Telegram MCP Server (Telethon + MTProto).

If tools return auth errors, the session needs to be regenerated:
1. Run: cd /root/bot-mcp && python3 login.py
2. Restart the MCP server.

Use telegram_status to check the current connection state before running other tools."""

mcp = MCPServer("telegram-mcp", instructions=MCP_INSTRUCTIONS, lifespan=lifespan)


@mcp.tool()
async def telegram_status() -> str:
    """
    Checks the current Telegram connection state, session validity, and environment configuration.
    Call this first to diagnose auth issues before using other tools.
    """
    import os
    status = {
        "test_mode": os.environ.get("TELEGRAM_TEST_MODE", "false"),
        "api_id_set": bool(os.environ.get("TELEGRAM_API_ID")),
        "api_hash_set": bool(os.environ.get("TELEGRAM_API_HASH")),
        "session_set": bool(os.environ.get("TELEGRAM_SESSION")),
        "default_bot": os.environ.get("DEFAULT_TARGET_BOT", "(not set)"),
    }

    if not status["session_set"]:
        status["connected"] = False
        status["error"] = "No TELEGRAM_SESSION in .env. Run: cd /root/bot-mcp && python3 login.py"
        return json.dumps(status, indent=2)

    try:
        client = await telegram_service.get_client()
        me = await client.get_me()
        status["connected"] = True
        phone_masked = None
        if me.phone:
            p = str(me.phone)
            phone_masked = f"+{p[:2]} {'*' * (len(p) - 6)} {p[-4:]}" if len(p) > 6 else ("*" * len(p))

        status["user"] = {
            "id": me.id,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "username": me.username,
            "phone": phone_masked,
        }
    except Exception as e:
        status["connected"] = False
        err = str(e)
        if "AuthKeyDuplicated" in err or "authorization key" in err.lower():
            status["error"] = "Session permanently revoked (AuthKeyDuplicatedError). Run: cd /root/bot-mcp && python3 login.py"
        elif "not authorized" in err.lower():
            status["error"] = "Session expired or invalid. Run: cd /root/bot-mcp && python3 login.py"
        else:
            status["error"] = err

    return json.dumps(status, indent=2)


@mcp.tool()
async def telegram_execute_code(
    code: str,
    timeout_seconds: int = 30,
) -> str:
    """
    Executes arbitrary custom asynchronous Python code with direct access to the live Telethon client and MTProto API.
    Available pre-injected variables:
      - `client`: Authenticated Telethon TelegramClient instance (e.g. `await client.get_dialogs()`, `await client(...)`)
      - `service` / `telegram_service`: The TelegramService instance
      - `events`: telethon.events
      - `functions`: telethon.tl.functions (raw MTProto functions)
      - `types`: telethon.tl.types (raw MTProto types)
      - `asyncio`, `json`, `os`, `time`
    Stdout/stderr and return values are captured and returned in the JSON result.
    """
    try:
        res = await telegram_service.execute_code(code, timeout_seconds=timeout_seconds)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_command(
    bot_username: str,
    command: str,
    wait_response: bool = True,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends a bot command (e.g. /start, /help, /settings) to the target bot and optionally waits for response.
    """
    try:
        sent = await telegram_service.send_message(bot_username, command)
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_command": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_message(
    bot_username: str,
    text: str,
    reply_to_msg_id: Optional[int] = None,
    wait_response: bool = True,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends a text message or payload to the target bot or chat.
    """
    try:
        sent = await telegram_service.send_message(bot_username, text, reply_to_msg_id)
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_message": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_file(
    bot_username: str,
    file_path: str,
    caption: Optional[str] = None,
    reply_to_msg_id: Optional[int] = None,
    wait_response: bool = True,
    timeout_seconds: int = 15,
) -> str:
    """
    Sends a file, photo, document, voice note, or media to the bot and optionally waits for its response.
    """
    try:
        sent = await telegram_service.send_file(
            bot_username=bot_username,
            file_path=file_path,
            caption=caption,
            reply_to_msg_id=reply_to_msg_id,
        )
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_file": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_download_media(
    bot_username: str,
    message_id: int,
    output_dir: Optional[str] = None,
) -> str:
    """
    Downloads media (photo, document, audio, chart) attached to a bot's message to inspect or verify its content.
    """
    try:
        res = await telegram_service.download_media(
            bot_username=bot_username,
            message_id=message_id,
            output_dir=output_dir,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_click_inline_button(
    bot_username: str,
    message_id: Optional[int] = None,
    button_text: Optional[str] = None,
    button_index: Optional[int] = None,
    wait_update: bool = True,
) -> str:
    """
    Clicks an inline keyboard button on a specific bot message (or latest message if omitted).
    """
    try:
        res = await telegram_service.click_inline_button(
            bot_username=bot_username,
            message_id=message_id,
            button_text=button_text,
            button_index=button_index,
            wait_update=wait_update,
        )
        return json.dumps(
            {
                "status": "success",
                "action": "clicked_button",
                "message_id": res.get("message_id"),
                "popup_alert": res.get("popup_alert"),
                "updated_message": res.get("updated_message"),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_inline_query(
    bot_username: str,
    query: str,
) -> str:
    """
    Performs an inline query against the bot (e.g. '@my_bot search') and retrieves the list of returned inline results.
    """
    try:
        results = await telegram_service.inline_query(bot_username, query)
        return json.dumps(
            {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_and_verify(
    bot_username: str,
    input_text: str,
    expected_contains: str,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends text or command to the bot and asserts that the bot's reply contains expected text.
    """
    try:
        sent = await telegram_service.send_message(bot_username, input_text)
        reply = await telegram_service.wait_for_reply(
            bot_username,
            after_message_id=sent["id"],
            timeout_seconds=timeout_seconds,
        )

        if not reply:
            return json.dumps(
                {
                    "verified": False,
                    "reason": "Timeout waiting for bot response",
                    "sent": sent,
                },
                indent=2,
            )

        passed = expected_contains.lower() in reply.get("text", "").lower()

        return json.dumps(
            {
                "verified": passed,
                "expected": expected_contains,
                "received_text": reply.get("text", ""),
                "available_buttons": reply.get("buttons") or [],
                "message_id": reply.get("id"),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_run_test_suite(
    bot_username: str,
    steps: List[Dict[str, Any]],
) -> str:
    """
    Executes a multi-step test scenario against a bot with sleep/wait support in a single call.
    Supported actions in steps:
      - {"action": "send", "text": "/start"}
      - {"action": "send_file", "file_path": "/path/to/test.png", "caption": "Optional"}
      - {"action": "sleep", "seconds": 2.5}
      - {"action": "assert_reply", "contains": "Welcome", "timeout_seconds": 10}
      - {"action": "click_button", "text": "Settings", "message_id": 1234}
      - {"action": "clear_chat"}
    """
    try:
        report = await telegram_service.run_test_suite(bot_username, steps)
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_chat_history(
    bot_username: str,
    limit: int = 10,
) -> str:
    """
    Fetches recent message history, media details, and inline keyboard buttons from the chat with the bot.
    """
    try:
        history = await telegram_service.get_chat_history(bot_username, limit=limit)
        return json.dumps(
            {
                "status": "success",
                "count": len(history),
                "messages": history,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_clear_chat(
    bot_username: str,
) -> str:
    """
    Clears the chat dialog history with the target bot for clean testing states.
    """
    try:
        await telegram_service.clear_chat(bot_username)
        return json.dumps(
            {
                "status": "success",
                "message": f"Chat dialog with {bot_username} cleared successfully.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


if __name__ == "__main__":
    def handle_signal(*args):
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    mcp.run()
