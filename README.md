# Telegram Bot Testing & Verification MCP Server 🤖🧪

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io)
[![Telethon](https://img.shields.io/badge/Telethon-MTProto-blue.svg)](https://github.com/LonamiWebs/Telethon)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (**MCP**) server that allows AI Coding Agents (such as Antigravity, Claude Desktop, Cursor, and custom agent backends) to autonomously **interact with, test, click buttons on, and verify Telegram bots** end-to-end.

> 📖 **AI Agents**: See the dedicated [**AI Agent Testing Guide**](docs/AGENT_GUIDE.md) for tool selection workflows, test suites, and best practices.

> [!TIP]
> **Environment Recommendation**: We strongly recommend using the **Test Server** (`TELEGRAM_TEST_MODE=true`) for bot development and automated testing because it carries **zero risk to your main personal Telegram account**.
> *Note: Make sure your target bot and user account are on the **same environment** (Test Server bot ↔ Test Server account, or Prod bot ↔ Prod account), as Telegram test and production networks are completely isolated.*

---

## 🌟 Features

* **Command & Message Dispatch**: Send commands (`/start`, `/help`, `/settings`) and text payloads to any target bot.
* **Inline Keyboard Navigation**: Click inline callback buttons (`CallbackQuery`), trigger button menus, and inspect in-place message updates.
* **Multi-Step Test Suite Runner (`telegram_run_test_suite`)**: Execute full regression test scenarios with assertions and `sleep` delays in a single tool call.
* **Media & File Testing**: Send photos, documents, audio, or PDFs to bots, and download returned media to verify generated files.
* **Inline Query Mode**: Test `@bot query` inline modes and inspect returned inline articles and preview metadata.
* **Python Code Execution Sandbox (`telegram_execute_code`)**: Run custom asynchronous Python scripts with direct access to the live `TelegramClient` and raw MTProto functions.
* **Clean State Management**: Clear dialog history before/after test runs for idempotent testing.

---

## 🚀 Quickstart

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Fire162/telegram-bot-mcp.git
cd telegram-bot-mcp
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Add your Telegram API credentials from [my.telegram.org](https://my.telegram.org):
```ini
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_TEST_MODE=false
```

### 3. Generate Session (One-Time Login)

Run the interactive login script:
```bash
python3 login.py
```
* Enter your phone number and the verification code sent to your Telegram app.
* The script saves your `TELEGRAM_SESSION` string automatically into `.env`.

### 4. Run the MCP Server

```bash
python3 server.py
```

---

## 🔌 Connecting to AI Agents

### Antigravity CLI (`agy`) / Gemini
The repository includes a pre-configured `.agents/plugins/telegram-bot/` plugin. Any `agy` session started in this workspace will automatically discover and load the tools.

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "telegram-bot": {
      "command": "python3",
      "args": ["/path/to/telegram-bot-mcp/server.py"],
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

---

## 🛠️ MCP Tools Reference

| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `telegram_send_command` | `bot_username`, `command`, `wait_response?`, `timeout_seconds?` | Sends a command and waits for reply. |
| `telegram_send_message` | `bot_username`, `text`, `reply_to_msg_id?`, `wait_response?` | Sends text payloads or queries. |
| `telegram_click_inline_button` | `bot_username`, `message_id?`, `button_text?`, `button_index?` | Clicks inline buttons and returns updated message state. |
| `telegram_send_file` | `bot_username`, `file_path`, `caption?` | Uploads images/documents/audio. |
| `telegram_download_media` | `bot_username`, `message_id`, `output_dir?` | Downloads media from bot messages. |
| `telegram_inline_query` | `bot_username`, `query` | Performs inline queries (`@bot query`). |
| `telegram_send_and_verify` | `bot_username`, `input_text`, `expected_contains` | Convenience single-step assertion. |
| `telegram_run_test_suite` | `bot_username`, `steps` | Runs multi-step test workflows with `sleep` and assertions. |
| `telegram_execute_code` | `code`, `timeout_seconds?` | Executes arbitrary Python code with live Telethon client access. |
| `telegram_get_chat_history` | `bot_username`, `limit?` | Fetches recent conversation history. |
| `telegram_clear_chat` | `bot_username` | Clears conversation dialog for clean tests. |

---

## 🧪 Example Test Suite Scenario

```json
[
  {"action": "send", "text": "/start"},
  {"action": "sleep", "seconds": 1.0},
  {"action": "assert_reply", "contains": "Welcome to my bot!"},
  {"action": "click_button", "text": "Settings"},
  {"action": "sleep", "seconds": 0.5},
  {"action": "assert_reply", "contains": "Notification Preferences"}
]
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
