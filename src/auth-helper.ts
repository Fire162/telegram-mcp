import { TelegramClient } from "telegram";
import { StringSession } from "telegram/sessions/index.js";
import readline from "readline";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";

dotenv.config();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const askQuestion = (query: string): Promise<string> =>
  new Promise((resolve) => rl.question(query, resolve));

async function main() {
  console.log("==========================================");
  console.log("   Telegram MCP Session Generator         ");
  console.log("==========================================");

  let apiIdStr = process.env.TELEGRAM_API_ID;
  let apiHash = process.env.TELEGRAM_API_HASH;
  const isTestMode = process.env.TELEGRAM_TEST_MODE !== "false";

  if (!apiIdStr) {
    apiIdStr = await askQuestion("Enter your TELEGRAM_API_ID (from my.telegram.org): ");
  }
  if (!apiHash) {
    apiHash = await askQuestion("Enter your TELEGRAM_API_HASH (from my.telegram.org): ");
  }

  const apiId = parseInt(apiIdStr.trim(), 10);
  apiHash = apiHash.trim();

  console.log(`\nConnecting to Telegram (${isTestMode ? "TEST Server (DC 2)" : "PRODUCTION Server"})...`);

  const client = new TelegramClient(new StringSession(""), apiId, apiHash, {
    connectionRetries: 5,
    useIPV6: false,
    testServers: isTestMode,
  });

  await client.start({
    phoneNumber: async () => {
      if (isTestMode) {
        const defaultNum = "9996621111";
        const answer = await askQuestion(
          `Enter Test Phone Number (default: ${defaultNum}): `
        );
        return answer.trim() || defaultNum;
      }
      return await askQuestion("Enter your phone number (e.g. +1234567890): ");
    },
    password: async () => await askQuestion("Enter your 2FA password (if enabled): "),
    phoneCode: async () => {
      if (isTestMode) {
        console.log("Using default test server OTP: 22222");
        return "22222";
      }
      return await askQuestion("Enter the verification code received via Telegram: ");
    },
    onError: (err) => console.error("Login Error:", err),
  });

  const sessionString = (client.session as StringSession).save();
  console.log("\nAuthentication successful!");
  console.log("\nYour Session String:\n" + sessionString + "\n");

  const envPath = path.resolve(process.cwd(), ".env");
  let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf-8") : "";

  if (envContent.includes("TELEGRAM_SESSION=")) {
    envContent = envContent.replace(
      /TELEGRAM_SESSION=.*/g,
      `TELEGRAM_SESSION=${sessionString}`
    );
  } else {
    envContent += `\nTELEGRAM_SESSION=${sessionString}`;
  }

  if (!envContent.includes("TELEGRAM_API_ID=")) {
    envContent += `\nTELEGRAM_API_ID=${apiId}`;
  }
  if (!envContent.includes("TELEGRAM_API_HASH=")) {
    envContent += `\nTELEGRAM_API_HASH=${apiHash}`;
  }
  if (!envContent.includes("TELEGRAM_TEST_MODE=")) {
    envContent += `\nTELEGRAM_TEST_MODE=${isTestMode ? "true" : "false"}`;
  }

  fs.writeFileSync(envPath, envContent.trim() + "\n");
  console.log(`Saved session credentials to: ${envPath}`);

  rl.close();
  await client.disconnect();
  process.exit(0);
}

main().catch((err) => {
  console.error("Fatal error during auth:", err);
  rl.close();
  process.exit(1);
});
