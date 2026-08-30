# Contributing to telegram-bot-mcp

Thank you for your interest in contributing to `telegram-bot-mcp`. This project provides an MCP server for AI coding agents to test and interact with Telegram bots.

## Development Setup

1. **Prerequisites**:
   - Node.js (v20+ recommended)
   - `pnpm` (preferred package manager)

2. **Installation**:
   ```bash
   pnpm install
   ```

3. **Environment Setup**:
   - Copy `.env.example` to `.env`.
   - Provide `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from [my.telegram.org](https://my.telegram.org).
   - Set `TELEGRAM_TEST_MODE=true` to test against Telegram's Test Server (DC 2) without using personal phone numbers.
   - Run the auth helper to generate a session string:
     ```bash
     pnpm login
     ```

4. **Building**:
   ```bash
   pnpm build
   ```

5. **Running Locally**:
   ```bash
   pnpm dev
   ```

## Code Guidelines

- Write clean, maintainable TypeScript with strict type checking enabled.
- Avoid unnecessary abstractions or adding unneeded dependencies.
- Keep MCP tool schemas in `src/tools.ts` clear with descriptive parameter documentation for LLMs.
- Document any workflow or architecture updates in `AGENT.md` and append notable updates to `CHANGELOG.md`.

## Submitting Changes

- Ensure TypeScript compiles cleanly with `pnpm build`.
- Create concise, meaningful commits.
