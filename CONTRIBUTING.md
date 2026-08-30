# Contributing to telegram-bot-mcp

Thank you for your interest in contributing to `telegram-bot-mcp`! This project provides a Model Context Protocol (MCP) server that empowers AI coding agents to autonomously test, interact with, click buttons on, and verify Telegram bots.

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Python 3.10+**
- `pip` / virtual environment

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Fire162/telegram-bot-mcp.git
cd telegram-bot-mcp
pip install -r requirements.txt
```

### 3. Environment Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Obtain your `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from [my.telegram.org](https://my.telegram.org) and add them to `.env`.
3. Set `TELEGRAM_TEST_MODE=true` for testing on Telegram's Sandbox DC 2 (or `false` for production).
4. Run the interactive login helper to generate your session string:
   ```bash
   python3 login.py
   ```

### 4. Running the MCP Server Locally
```bash
python3 server.py
```

---

## 📋 Code & Contribution Guidelines

- **Architecture**: Keep MTProto interactions in `telegram_service.py` and MCP tool registrations in `server.py`.
- **Typing & Clean Code**: Use Python type hints (`typing`) and clear docstrings for all MCP tools so AI agents can parse their JSON schemas accurately.
- **Dependencies**: Keep dependencies minimal (`mcp`, `telethon`, `python-dotenv`). Do not add third-party libraries for trivial logic.
- **Security First**: Never commit `.env`, session strings, or API credentials.
- **Documentation**: If adding a new tool or capability, update:
  1. `server.py` & `telegram_service.py`
  2. `AGENT.md`
  3. `docs/AGENT_GUIDE.md`
  4. `.agents/plugins/telegram-bot/rules/AGENTS.md`
  5. `CHANGELOG.md` with timestamps formatted in `Asia/Kolkata` timezone.

---

## 🚀 Submitting Pull Requests

1. Create a descriptive feature branch:
   ```bash
   git checkout -b feat/my-new-tool
   ```
2. Verify code syntax and functionality:
   ```bash
   python3 -c "import py_compile; py_compile.compile('server.py', doraise=True); py_compile.compile('telegram_service.py', doraise=True)"
   ```
3. Commit with concise, meaningful commit messages.
4. Push your branch and open a Pull Request on GitHub.
