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
  console.log("   Telegram Bot MCP - Session Login       ");
  console.log("==========================================");

  let apiIdStr = process.env.TELEGRAM_API_ID;
  let apiHash = process.env.TELEGRAM_API_HASH;

  if (!apiIdStr) {
    apiIdStr = await askQuestion("Enter your TELEGRAM_API_ID: ");
  }
  if (!apiHash) {
    apiHash = await askQuestion("Enter your TELEGRAM_API_HASH: ");
  }

  const serverChoice = await askQuestion(
    "Choose Telegram Network:\n  [1] Production Server (Real Telegram Network - Recommended)\n  [2] Test Server (DC 2 Sandbox)\nEnter 1 or 2 (default: 1): "
  );

  const isTestMode = serverChoice.trim() === "2";
  const apiId = parseInt(apiIdStr.trim(), 10);
  apiHash = apiHash.trim();

  console.log(
    `\nConnecting to Telegram ${isTestMode ? "TEST Server (DC 2)" : "PRODUCTION Server"}...`
  );

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
      return await askQuestion("Enter your phone number with country code (e.g. +919876543210): ");
    },
    password: async () => await askQuestion("Enter your 2FA password (leave empty if not enabled): "),
    phoneCode: async () => {
      if (isTestMode) {
        const code = await askQuestion("Enter Test OTP Code (default: 22222): ");
        return code.trim() || "22222";
      }
      return await askQuestion("Enter the verification code received on Telegram: ");
    },
    firstAndLastNames: async () => ["Agent", "Tester"],
    onError: (err) => console.error("Login Error:", err?.message || err),
  });

  const sessionString = (client.session as StringSession).save();
  console.log("\n==========================================");
  console.log("🎉 Authentication successful!");
  console.log("==========================================");

  const envPath = path.resolve(process.cwd(), ".env");
  let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf-8") : "";

  const updateOrAppend = (key: string, value: string) => {
    const regex = new RegExp(`^${key}=.*$`, "m");
    if (regex.test(envContent)) {
      envContent = envContent.replace(regex, `${key}=${value}`);
    } else {
      envContent += `\n${key}=${value}`;
    }
  };

  updateOrAppend("TELEGRAM_API_ID", String(apiId));
  updateOrAppend("TELEGRAM_API_HASH", apiHash);
  updateOrAppend("TELEGRAM_SESSION", sessionString);
  updateOrAppend("TELEGRAM_TEST_MODE", isTestMode ? "true" : "false");

  fs.writeFileSync(envPath, envContent.trim() + "\n");
  console.log(`\n✅ Saved session string into: ${envPath}`);
  console.log("You can now start the MCP server using: pnpm start\n");

  rl.close();
  await client.disconnect();
  process.exit(0);
}

main().catch((err) => {
  console.error("Fatal error during auth:", err);
  rl.close();
  process.exit(1);
});
