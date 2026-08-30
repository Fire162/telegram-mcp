# 📋 Changelog

All notable changes to **`telegram-bot-mcp`** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), and includes timestamps in `Asia/Kolkata` (IST).

---

## [v1.2.0] — 2026-08-30 (15:40 IST)

### 🚀 New Features
* **Live Python Code Execution Sandbox (`telegram_execute_code`)**: Added direct async execution tool allowing AI agents to run custom Telethon and MTProto scripts on the authenticated client.
* **Multi-Step Test Suite Runner (`telegram_run_test_suite`)**: Executes complete end-to-end regression workflows with assertions and configurable `sleep` intervals.
* **Media & Document Verification**: Added `telegram_send_file` (upload photos, docs, audio) and `telegram_download_media` (inspect bot-generated media locally).
* **Inline Query Mode (`telegram_inline_query`)**: Added simulation and result parsing for `@bot query` inline modes.

### 🛡️ Security & Environment
* **Environment Alignment Rule**: Enforced strict DC 2 Sandbox isolation for test accounts and production isolation for live accounts.
* **Secret Sanitization**: Verified automated scans for `.env` exclusion and secret leak prevention.

### 🧹 Refactoring & Cleanup
* **Pure Python Migration**: Complete transition to Python 3 + Telethon + official MCP SDK (`MCPServer`).
* **Housekeeping**: Removed deprecated TypeScript build artifacts (`src/`, `package.json`, `tsconfig.json`).
* **Documentation**: Added dedicated [`docs/AGENT_GUIDE.md`](docs/AGENT_GUIDE.md) and modernized [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## [v1.0.0] — 2026-08-30 (14:04 IST)

### 🚀 Initial Release
* First release of the Telegram Bot Testing MCP Server.
* Supported command dispatch (`/start`, `/help`), message sending, and inline keyboard button clicking via MTProto.
* Integrated workspace discovery for Antigravity (`agy` CLI).
