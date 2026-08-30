#!/usr/bin/env python3
import json
import asyncio
from typing import Optional
from mcp.server.mcpserver import MCPServer
from telegram_service import telegram_service

mcp = MCPServer("telegram-bot-mcp")


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
    Sends a text message or payload to the target bot.
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
async def telegram_click_inline_button(
    bot_username: str,
    message_id: int,
    button_text: Optional[str] = None,
    button_index: Optional[int] = None,
    wait_update: bool = True,
) -> str:
    """
    Clicks an inline keyboard button on a specific bot message by label or index.
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
                "popup_alert": res.get("popup_alert"),
                "updated_message": res.get("updated_message"),
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
async def telegram_get_chat_history(
    bot_username: str,
    limit: int = 10,
) -> str:
    """
    Fetches recent message history and inline keyboard buttons from the chat with the bot.
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
    mcp.run()
