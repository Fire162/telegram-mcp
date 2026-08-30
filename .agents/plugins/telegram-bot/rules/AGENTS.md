# Telegram Bot Testing Guide

When testing or verifying Telegram bots in this workspace, use the available `telegram-bot` MCP tools:

- `telegram_execute_code(code, timeout_seconds)`: Executes arbitrary Python code with direct access to the live `client` (Telethon instance), `functions`, `events`, and `types` for full control.
- `telegram_send_command(bot_username, command)`: Sends `/start`, `/help`, etc. and receives the bot's reply.
- `telegram_send_message(bot_username, text)`: Sends text payloads or queries to the bot.
- `telegram_send_file(bot_username, file_path, caption)`: Sends photos, documents, audio, or test files to the bot.
- `telegram_download_media(bot_username, message_id)`: Downloads media sent by the bot for inspection.
- `telegram_click_inline_button(bot_username, message_id, button_text)`: Clicks inline keyboard buttons by name or index.
- `telegram_inline_query(bot_username, query)`: Tests inline query results (`@bot query`).
- `telegram_send_and_verify(bot_username, input_text, expected_contains)`: Asserts expected response patterns from the bot.
- `telegram_run_test_suite(bot_username, steps)`: Runs full multi-step test workflows with `sleep`, assertions, file uploads, and button clicks in one call.
- `telegram_get_chat_history(bot_username)`: Reads recent conversation history.
- `telegram_clear_chat(bot_username)`: Clears chat history for clean test states.
