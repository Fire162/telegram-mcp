# AGENT.md - Telegram Bot Testing MCP Server Guide (Python + Telethon)

This guide documents the architecture, setup, development workflow, and conventions for the `telegram-bot-mcp` project.

---

## 1. Project Overview

`telegram-bot-mcp` is a Model Context Protocol (MCP) server built with Python (`mcp` / `MCPServer`) and `Telethon`. It enables AI coding agents to interact with, test, and verify Telegram bots. It uses Telegram's MTProto protocol to perform end-to-end actions such as sending commands, reading formatted responses, and clicking inline keyboard buttons.

---

## 2. Directory Structure

```
/root/bot-mcp
├── server.py              # Main MCP server entrypoint and tool definitions
├── telegram_service.py    # Telethon MTProto client wrapper and interaction methods
├── login.py               # Interactive CLI helper for Telegram authentication
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── AGENT.md               # AI agent reference documentation
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

3. `telegram_click_inline_button`
   - **Arguments**: `bot_username`, `message_id`, `button_text?`, `button_index?`, `wait_update` (default: `True`)
   - **Usage**: Triggers callback queries on inline keyboard buttons attached to a bot message.

4. `telegram_send_and_verify`
   - **Arguments**: `bot_username`, `input_text`, `expected_contains`, `timeout_seconds` (default: `10`)
   - **Usage**: Convenience assertion tool for end-to-end verification.

5. `telegram_get_chat_history`
   - **Arguments**: `bot_username`, `limit` (default: `10`)
   - **Usage**: Retrieves recent messages and message metadata.

6. `telegram_clear_chat`
   - **Arguments**: `bot_username`
   - **Usage**: Deletes dialog history for clean testing states.

---

## 5. Client MCP Configuration Example

To register this server in an MCP host (such as Antigravity, Claude Desktop, or custom agent runner):

```json
{
  "mcpServers": {
    "telegram-bot": {
      "command": "python3",
      "args": ["/root/bot-mcp/server.py"],
      "env": {
        "TELEGRAM_API_ID": "your_api_id",
        "TELEGRAM_API_HASH": "your_api_hash",
        "TELEGRAM_SESSION": "your_session_string",
        "TELEGRAM_TEST_MODE": "false"
      }
    }
  }
}
```
