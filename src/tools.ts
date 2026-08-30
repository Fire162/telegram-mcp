import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { telegramService } from "./telegram.js";

export function registerTools(server: McpServer) {
  // 1. Send Command (e.g. /start, /help)
  server.tool(
    "telegram_send_command",
    "Sends a bot command (e.g., /start, /help, /settings) to the target bot and optionally waits for its response.",
    {
      bot_username: z
        .string()
        .describe("The Telegram bot username (e.g. '@my_bot' or 'my_bot')"),
      command: z
        .string()
        .describe("The command to send, e.g. '/start' or '/help'"),
      wait_response: z
        .boolean()
        .default(true)
        .describe("Whether to wait for the bot's response"),
      timeout_seconds: z
        .number()
        .default(10)
        .describe("Max seconds to wait for bot response (default: 10)"),
    },
    async ({ bot_username, command, wait_response, timeout_seconds }) => {
      try {
        const sent = await telegramService.sendMessage(bot_username, command);
        let response = null;

        if (wait_response) {
          response = await telegramService.waitForReply(
            bot_username,
            sent.id,
            timeout_seconds
          );
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  status: "success",
                  sent_command: sent,
                  bot_response: response || (wait_response ? "Timeout waiting for response" : null),
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // 2. Send Message
  server.tool(
    "telegram_send_message",
    "Sends text or payload to the target bot.",
    {
      bot_username: z.string().describe("The Telegram bot username"),
      text: z.string().describe("Text content to send to the bot"),
      reply_to_msg_id: z.number().optional().describe("Optional message ID to reply to"),
      wait_response: z.boolean().default(true).describe("Whether to wait for the bot's response"),
      timeout_seconds: z.number().default(10).describe("Max seconds to wait for bot response"),
    },
    async ({ bot_username, text, reply_to_msg_id, wait_response, timeout_seconds }) => {
      try {
        const sent = await telegramService.sendMessage(bot_username, text, reply_to_msg_id);
        let response = null;

        if (wait_response) {
          response = await telegramService.waitForReply(
            bot_username,
            sent.id,
            timeout_seconds
          );
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  status: "success",
                  sent_message: sent,
                  bot_response: response || (wait_response ? "Timeout waiting for response" : null),
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // 3. Click Inline Button
  server.tool(
    "telegram_click_inline_button",
    "Clicks an inline keyboard button on a specific bot message.",
    {
      bot_username: z.string().describe("The Telegram bot username"),
      message_id: z.number().describe("The message ID containing the inline keyboard"),
      button_text: z
        .string()
        .optional()
        .describe("The exact text label of the button to click"),
      button_index: z
        .number()
        .optional()
        .describe("Zero-based index of the button (if button_text is not provided)"),
      wait_update: z
        .boolean()
        .default(true)
        .describe("Whether to wait for the message to be edited/updated after the click"),
    },
    async ({ bot_username, message_id, button_text, button_index, wait_update }) => {
      try {
        const res = await telegramService.clickInlineButton(bot_username, message_id, {
          buttonText: button_text,
          buttonIndex: button_index,
          waitUpdate: wait_update,
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  status: "success",
                  action: "clicked_button",
                  popup_alert: res.result || null,
                  updated_message: res.updatedMessage,
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // 4. Send and Verify Assertion
  server.tool(
    "telegram_send_and_verify",
    "Sends text/command to the bot and asserts that the bot's reply contains expected text.",
    {
      bot_username: z.string().describe("The Telegram bot username"),
      input_text: z.string().describe("The command or message to send"),
      expected_contains: z
        .string()
        .describe("Substring or pattern expected to be in the bot's response"),
      timeout_seconds: z.number().default(10).describe("Max timeout in seconds"),
    },
    async ({ bot_username, input_text, expected_contains, timeout_seconds }) => {
      try {
        const sent = await telegramService.sendMessage(bot_username, input_text);
        const reply = await telegramService.waitForReply(
          bot_username,
          sent.id,
          timeout_seconds
        );

        if (!reply) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(
                  {
                    verified: false,
                    reason: "Timeout waiting for bot response",
                    sent,
                  },
                  null,
                  2
                ),
              },
            ],
          };
        }

        const passed = reply.text.toLowerCase().includes(expected_contains.toLowerCase());

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  verified: passed,
                  expected: expected_contains,
                  received_text: reply.text,
                  available_buttons: reply.buttons || [],
                  message_id: reply.id,
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // 5. Get Chat History
  server.tool(
    "telegram_get_chat_history",
    "Fetches recent message history with the specified bot.",
    {
      bot_username: z.string().describe("The Telegram bot username"),
      limit: z.number().default(10).describe("Number of recent messages to fetch (default: 10)"),
    },
    async ({ bot_username, limit }) => {
      try {
        const history = await telegramService.getChatHistory(bot_username, limit);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "success", count: history.length, messages: history }, null, 2),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // 6. Clear Chat History
  server.tool(
    "telegram_clear_chat",
    "Clears the chat dialog history with the target bot for clean test runs.",
    {
      bot_username: z.string().describe("The Telegram bot username"),
    },
    async ({ bot_username }) => {
      try {
        await telegramService.clearChat(bot_username);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "success", message: `Chat with ${bot_username} cleared.` }),
            },
          ],
        };
      } catch (err: any) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "error", message: err?.message || String(err) }),
            },
          ],
          isError: true,
        };
      }
    }
  );
}
