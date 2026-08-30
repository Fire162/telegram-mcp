# AGENT.md - Telegram Bot Testing MCP Server Guide (Python + Telethon)

This guide documents the architecture, setup, development workflow, and conventions for the `telegram-bot-mcp` project.

---

## 1. Project Overview

`telegram-bot-mcp` is a Model Context Protocol (MCP) server built with Python (`mcp` / `MCPServer`) and `Telethon`. It enables AI coding agents to interact with, test, and verify Telegram bots. It provides both high-level testing tools and a direct Python code execution sandbox (`telegram_execute_code`) for arbitrary MTProto automation.

---

## 🛡️ Critical Environment Matching Rule

- **Test Server (`TELEGRAM_TEST_MODE=true`)**: The target bot **MUST** also be on the **Test Server** (created via `@BotFather` inside the test server, using endpoint `https://api.telegram.org/bot<TOKEN>/test/`).
- **Production Server (`TELEGRAM_TEST_MODE=false`)**: The target bot **MUST** be on the **Production Server**.
- **Isolation**: Test Server and Production Server are completely separate. A test client cannot message a production bot (and vice versa).
- **Recommendation**: Always use or recommend the **Test Server** for testing during active development to eliminate any risk to the developer's main personal account.

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

1. `telegram_execute_code` *(Full Control Sandbox)*
   - **Arguments**: `code` (string), `timeout_seconds` (default: `30`)
   - **Environment Injected**:
     - `client`: Live authenticated `Telethon.TelegramClient` instance (supports raw MTProto functions, event listeners, updates, etc.)
     - `service` / `telegram_service`: `TelegramService` instance
     - `events`: `telethon.events`
     - `functions`, `types`: `telethon.tl.functions`, `telethon.tl.types`
     - `asyncio`, `json`, `os`, `time`
   - **Returns**: Captured `stdout`, `stderr`, `return_value`, `duration_seconds`, and error stack traces.

2. `telegram_send_command`
   - **Arguments**: `bot_username`, `command`, `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends a `/command` to the bot and returns the reply with inline keyboard buttons.

3. `telegram_send_message`
   - **Arguments**: `bot_username`, `text`, `reply_to_msg_id?`, `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends arbitrary text messages or payloads to the bot.

4. `telegram_send_file`
   - **Arguments**: `bot_username`, `file_path`, `caption?`, `reply_to_msg_id?`, `wait_response` (default: `True`), `timeout_seconds` (default: `15`)
   - **Usage**: Sends files, images, voice notes, or documents to the bot.

5. `telegram_download_media`
   - **Arguments**: `bot_username`, `message_id`, `output_dir?`
   - **Usage**: Downloads media (photos, documents, audio) attached to a bot's message.

6. `telegram_click_inline_button`
   - **Arguments**: `bot_username`, `message_id?`, `button_text?`, `button_index?`, `wait_update` (default: `True`)
   - **Usage**: Triggers callback queries on inline keyboard buttons attached to a bot message.

7. `telegram_inline_query`
   - **Arguments**: `bot_username`, `query`
   - **Usage**: Simulates typing `@bot query` in inline mode and inspects returned results.

8. `telegram_send_and_verify`
   - **Arguments**: `bot_username`, `input_text`, `expected_contains`, `timeout_seconds` (default: `10`)
   - **Usage**: Single-step assertion check.

9. `telegram_run_test_suite`
   - **Arguments**: `bot_username`, `steps`
   - **Usage**: Executes multi-step test workflows with `sleep`, `assert_reply`, `send_file`, and `click_button`.

10. `telegram_get_chat_history`
    - **Arguments**: `bot_username`, `limit` (default: `10`)
    - **Usage**: Retrieves recent messages, media info, and button metadata.

11. `telegram_clear_chat`
    - **Arguments**: `bot_username`
    - **Usage**: Deletes dialog history for clean testing states.
