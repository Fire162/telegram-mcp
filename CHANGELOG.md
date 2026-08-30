# Changelog

All notable changes to the `telegram-bot-mcp` project will be documented in this file.

The format is based on `[YYYY-MM-DD]{HH:mm:ss} Title: Description #optional extra notes` in the `Asia/Kolkata` timezone.

---

[2026-08-30]{14:04:35} Initial Release: Implemented Model Context Protocol (MCP) server for automated Telegram bot testing and verification supporting MTProto, Test Server DC 2, command dispatch, and inline keyboard button interactions. #initial-release
[2026-08-30]{14:58:00} Architecture Migration: Migrated MCP server core and client layer to Python 3 with Telethon and MCP SDK (MCPServer) for robust cross-platform MTProto and bot verification support. #python-telethon-migration
[2026-08-30]{15:10:00} Feature Expansion: Added multi-step test suite runner (telegram_run_test_suite) with configurable sleep/wait actions, media upload/download, and inline query testing. #test-suite-runner
[2026-08-30]{15:16:00} Code Execution Sandbox: Added telegram_execute_code tool allowing AI agents to run arbitrary asynchronous Python scripts with live Telethon client and MTProto access for maximum control. #code-execution-sandbox
