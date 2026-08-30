# Telegram Bot Testing Guide

When testing or verifying Telegram bots in this workspace, use the available `telegram-bot` MCP tools:

- `telegram_send_command(bot_username, command)`: Sends `/start`, `/help`, etc. and receives the bot's reply.
- `telegram_send_message(bot_username, text)`: Sends text payloads or queries to the bot.
- `telegram_click_inline_button(bot_username, message_id, button_text)`: Clicks inline keyboard buttons by name or index.
- `telegram_send_and_verify(bot_username, input_text, expected_contains)`: Asserts expected response patterns from the bot.
- `telegram_get_chat_history(bot_username)`: Reads recent conversation history.
- `telegram_clear_chat(bot_username)`: Clears chat history for clean test states.
