import dotenv from "dotenv";

dotenv.config();

export interface AppConfig {
  apiId: number;
  apiHash: string;
  session: string;
  testMode: boolean;
  defaultTargetBot?: string;
}

export function getConfig(): AppConfig {
  const apiIdStr = process.env.TELEGRAM_API_ID;
  const apiHash = process.env.TELEGRAM_API_HASH;
  const session = process.env.TELEGRAM_SESSION || "";
  const testMode = process.env.TELEGRAM_TEST_MODE !== "false";
  const defaultTargetBot = process.env.DEFAULT_TARGET_BOT;

  if (!apiIdStr || !apiHash) {
    console.error("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in environment variables.");
  }

  const apiId = apiIdStr ? parseInt(apiIdStr, 10) : 0;

  return {
    apiId,
    apiHash: apiHash || "",
    session,
    testMode,
    defaultTargetBot,
  };
}
