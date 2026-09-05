# Telegram Bot Testing Guide

## 🛡️ Critical Environment Matching Rule
- **Test Server (`TELEGRAM_TEST_MODE=true`)**: The target bot **MUST** also be on the **Test Server** (created via `@BotFather` inside the test server, using endpoint `https://api.telegram.org/bot<TOKEN>/test/`).
- **Production Server (`TELEGRAM_TEST_MODE=false`)**: The target bot **MUST** be on the **Production Server**.
- **Isolation**: Test Server and Production Server are completely separate. A test client cannot message a production bot (and vice versa).
- **Recommendation**: Always recommend using the **Test Server** for testing to eliminate any risk to the user's main personal Telegram account.

---

## Available MCP Tools:
- `telegram_status()`: Checks connection health, session validity, and environment config.
- `telegram_execute_code(code, timeout_seconds)`: Executes arbitrary Python code with direct access to the live `client` (Telethon instance), `functions`, `events`, and `types` for full control.
- `telegram_send_command(bot_username, command)`: Sends `/start`, `/help`, etc. and receives the bot's reply.
- `telegram_send_message(bot_username, text, reply_to_msg_id, parse_mode)`: Sends text payloads or queries to the bot with Markdown/HTML formatting.
- `telegram_edit_message(bot_username, message_id, new_text, parse_mode)`: Edits previously sent messages.
- `telegram_delete_messages(bot_username, message_ids, revoke)`: Deletes messages by ID.
- `telegram_forward_messages(to_chat, from_chat, message_ids)`: Forwards messages between chats.
- `telegram_send_reaction(bot_username, message_id, reaction)`: Sends emoji reactions (👍, 🔥, etc.).
- `telegram_send_poll(bot_username, question, options, is_quiz, correct_option_id)`: Sends polls or quizzes.
- `telegram_mark_chat_read(bot_username, max_id)`: Marks chat messages as read.
- `telegram_list_dialogs(limit)`: Lists recent chats, bots, groups, and channels with unread counts.
- `telegram_search_messages(bot_username, query, limit)`: Searches message history by keyword.
- `telegram_send_file(bot_username, file_path, caption, voice_note)`: Sends photos, documents, audio, or circular voice notes.
- `telegram_download_media(bot_username, message_id)`: Downloads media sent by the bot for inspection.
- `telegram_click_inline_button(bot_username, message_id, button_text)`: Clicks inline keyboard buttons by name or index.
- `telegram_inline_query(bot_username, query)`: Tests inline query results (`@bot query`).
- `telegram_send_and_verify(bot_username, input_text, expected_contains)`: Asserts expected response patterns from the bot.
- `telegram_run_test_suite(bot_username, steps)`: Runs full multi-step test workflows with `sleep`, assertions, file uploads, and button clicks in one call.
- `telegram_get_chat_history(bot_username)`: Reads recent conversation history.
- `telegram_clear_chat(bot_username)`: Clears chat history for clean test states.
