import { TelegramClient, Api } from "telegram";
import { StringSession } from "telegram/sessions/index.js";
import { getConfig } from "./config.js";

export interface FormattedButton {
  text: string;
  data?: string;
  url?: string;
}

export interface FormattedMessage {
  id: number;
  date: number;
  sender: "user" | "bot" | "other";
  text: string;
  buttons?: FormattedButton[][];
}

export class TelegramService {
  private client: TelegramClient | null = null;
  private isConnecting: boolean = false;

  public async getClient(): Promise<TelegramClient> {
    if (this.client && this.client.connected) {
      return this.client;
    }

    if (this.isConnecting) {
      while (this.isConnecting) {
        await new Promise((r) => setTimeout(r, 100));
      }
      if (this.client && this.client.connected) {
        return this.client;
      }
    }

    this.isConnecting = true;
    try {
      const config = getConfig();
      if (!config.apiId || !config.apiHash) {
        throw new Error(
          "TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured in .env."
        );
      }

      const stringSession = new StringSession(config.session);
      this.client = new TelegramClient(stringSession, config.apiId, config.apiHash, {
        connectionRetries: 5,
        useIPV6: false,
        testServers: config.testMode,
      });

      await this.client.connect();
      return this.client;
    } finally {
      this.isConnecting = false;
    }
  }

  private cleanBotUsername(username: string): string {
    const config = getConfig();
    const target = username || config.defaultTargetBot || "";
    if (!target) {
      throw new Error(
        "Bot username was not provided and DEFAULT_TARGET_BOT is not configured in .env."
      );
    }
    return target.startsWith("@") ? target : `@${target}`;
  }

  private formatMessage(msg: any): FormattedMessage {
    const buttons: FormattedButton[][] = [];

    if (msg.replyMarkup?.rows) {
      for (const row of msg.replyMarkup.rows) {
        const rowButtons: FormattedButton[] = [];
        for (const btn of row.buttons) {
          rowButtons.push({
            text: btn.text,
            data: btn.data ? Buffer.from(btn.data).toString("utf-8") : undefined,
            url: btn.url || undefined,
          });
        }
        if (rowButtons.length > 0) {
          buttons.push(rowButtons);
        }
      }
    }

    return {
      id: msg.id,
      date: msg.date,
      sender: msg.out ? "user" : "bot",
      text: msg.message || "",
      buttons: buttons.length > 0 ? buttons : undefined,
    };
  }

  public async sendMessage(
    botUsername: string,
    text: string,
    replyToMsgId?: number
  ): Promise<FormattedMessage> {
    const client = await this.getClient();
    const target = this.cleanBotUsername(botUsername);

    const sent = await client.sendMessage(target, {
      message: text,
      replyTo: replyToMsgId,
    });

    return this.formatMessage(sent);
  }

  public async waitForReply(
    botUsername: string,
    afterMessageId?: number,
    timeoutSeconds: number = 10
  ): Promise<FormattedMessage | null> {
    const client = await this.getClient();
    const target = this.cleanBotUsername(botUsername);
    const peer = await client.getInputEntity(target);

    const startTime = Date.now();
    const timeoutMs = timeoutSeconds * 1000;

    while (Date.now() - startTime < timeoutMs) {
      const messages = await client.getMessages(peer, { limit: 5 });
      for (const msg of messages) {
        if (!msg.out && (!afterMessageId || msg.id > afterMessageId)) {
          return this.formatMessage(msg);
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    return null;
  }

  public async clickInlineButton(
    botUsername: string,
    messageId: number,
    options: { buttonText?: string; buttonIndex?: number; waitUpdate?: boolean } = {}
  ): Promise<{ success: boolean; result?: string; updatedMessage?: FormattedMessage | null }> {
    const client = await this.getClient();
    const target = this.cleanBotUsername(botUsername);
    const peer = await client.getInputEntity(target);

    const msgs = await client.getMessages(peer, { ids: [messageId] });
    const msg = msgs && msgs[0];
    if (!msg) {
      throw new Error(`Message with ID ${messageId} not found.`);
    }

    let clickResult: any = null;
    if (options.buttonText) {
      clickResult = await (msg as any).click({ text: options.buttonText });
    } else if (typeof options.buttonIndex === "number") {
      clickResult = await (msg as any).click(options.buttonIndex);
    } else {
      clickResult = await (msg as any).click(0);
    }

    let updatedMessage: FormattedMessage | null = null;
    if (options.waitUpdate !== false) {
      await new Promise((r) => setTimeout(r, 1000));
      const freshMsgs = await client.getMessages(peer, { ids: [messageId] });
      if (freshMsgs && freshMsgs[0]) {
        updatedMessage = this.formatMessage(freshMsgs[0]);
      }
    }

    return {
      success: true,
      result: typeof clickResult === "string" ? clickResult : undefined,
      updatedMessage,
    };
  }

  public async getChatHistory(
    botUsername: string,
    limit: number = 10
  ): Promise<FormattedMessage[]> {
    const client = await this.getClient();
    const target = this.cleanBotUsername(botUsername);
    const peer = await client.getInputEntity(target);

    const messages = await client.getMessages(peer, { limit });
    return messages.map((m) => this.formatMessage(m));
  }

  public async clearChat(botUsername: string): Promise<boolean> {
    const client = await this.getClient();
    const target = this.cleanBotUsername(botUsername);
    const peer = await client.getInputEntity(target);

    await client.invoke(
      new Api.messages.DeleteHistory({
        peer,
        maxId: 0,
        revoke: true,
      })
    );
    return true;
  }
}

export const telegramService = new TelegramService();
