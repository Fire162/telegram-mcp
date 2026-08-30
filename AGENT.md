# AGENT.md - Telegram Bot Testing MCP Server Guide (Python + Telethon)

This guide documents the architecture, setup, development workflow, and conventions for the `telegram-bot-mcp` project.

---

## 1. Project Overview

`telegram-bot-mcp` is a Model Context Protocol (MCP) server built with Python (`mcp` / `MCPServer`) and `Telethon`. It enables AI coding agents to interact with, test, and verify Telegram bots. It uses Telegram's MTProto protocol to perform end-to-end actions such as sending commands, reading formatted responses, uploading files, testing inline queries, and clicking inline keyboard buttons.

---

## 2. Directory Structure

```
/root/bot-mcp
├── server.py              # Main MCP server entrypoint and tool definitions
├── telegram_service.py    # Telethon MTProto client wrapper and interaction methods
├── login.py               # Interactive CLI helper for Telegram authentication
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── AGENT.md               # AI agent reference documentation
├── CHANGELOG.md           # Project history in Asia/Kolkata timezone
├── CONTRIBUTING.md        # Contribution guide
└── LICENSE                # MIT License
```

---

## 3. Development Commands

- **Install Dependencies**: `pip install -r requirements.txt`
- **Login / Generate Session**: `python3 login.py`
- **Run MCP Server**: `python3 server.py`

---

## 4. MCP Tools Reference

The server exposes the following tools:

1. `telegram_send_command`
   - **Arguments**: `bot_username`, `command`, `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends a `/command` to the bot and returns the sent message and bot's response with any inline keyboard buttons.

2. `telegram_send_message`
   - **Arguments**: `bot_username`, `text`, `reply_to_msg_id?`, `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends arbitrary text messages or payloads to the bot.

3. `telegram_send_file`
   - **Arguments**: `bot_username`, `file_path`, `caption?`, `reply_to_msg_id?`, `wait_response` (default: `True`), `timeout_seconds` (default: `15`)
   - **Usage**: Sends files, images, voice notes, or documents to the bot.

4. `telegram_download_media`
   - **Arguments**: `bot_username`, `message_id`, `output_dir?`
   - **Usage**: Downloads media (photos, documents, audio) attached to a bot's message to inspect its content.

5. `telegram_click_inline_button`
   - **Arguments**: `bot_username`, `message_id?` (optional, latest if omitted), `button_text?`, `button_index?`, `wait_update` (default: `True`)
   - **Usage**: Triggers callback queries on inline keyboard buttons attached to a bot message.

6. `telegram_inline_query`
   - **Arguments**: `bot_username`, `query`
   - **Usage**: Simulates typing `@bot query` in inline mode and inspects returned results.

7. `telegram_send_and_verify`
   - **Arguments**: `bot_username`, `input_text`, `expected_contains`, `timeout_seconds` (default: `10`)
   - **Usage**: Convenience assertion tool for single-step verification.

8. `telegram_run_test_suite`
   - **Arguments**: `bot_username`, `steps`
   - **Usage**: Executes a multi-step scenario in a single tool call with step types:
     - `send`: `{"action": "send", "text": "/start"}`
     - `send_file`: `{"action": "send_file", "file_path": "test.png", "caption": "..."}`
     - `sleep`: `{"action": "sleep", "seconds": 2.0}`
     - `assert_reply`: `{"action": "assert_reply", "contains": "Welcome", "timeout_seconds": 10}`
     - `click_button`: `{"action": "click_button", "text": "Settings", "message_id": 1234}`
     - `clear_chat`: `{"action": "clear_chat"}`

9. `telegram_get_chat_history`
   - **Arguments**: `bot_username`, `limit` (default: `10`)
   - **Usage**: Retrieves recent messages, media info, and button metadata.

10. `telegram_clear_chat`
    - **Arguments**: `bot_username`
    - **Usage**: Deletes dialog history for clean testing states.
