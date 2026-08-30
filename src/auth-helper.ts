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
  console.log("\n=======================================================");
  console.log("   Telegram Bot MCP - One-Time Account Login           ");
  console.log("=======================================================\n");

  const apiIdStr = process.env.TELEGRAM_API_ID;
  const apiHash = process.env.TELEGRAM_API_HASH;

  if (!apiIdStr || !apiHash) {
    console.error("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in .env file.");
    process.exit(1);
  }

  const apiId = parseInt(apiIdStr.trim(), 10);
  const client = new TelegramClient(new StringSession(""), apiId, apiHash.trim(), {
    connectionRetries: 5,
    useIPV6: false,
    testServers: false,
  });

  console.log("Connecting to Telegram Network...\n");

  await client.start({
    phoneNumber: async () => {
      const phone = await askQuestion("📱 Enter your phone number with country code (e.g. +919876543210): ");
      return phone.trim();
    },
    password: async () => {
      const pw = await askQuestion("🔑 Enter 2FA Password (press Enter if you don't have one): ");
      return pw.trim();
    },
    phoneCode: async () => {
      const code = await askQuestion("📩 Enter the code received in your Telegram App: ");
      return code.trim();
    },
    onError: (err) => console.error("⚠️ Error:", err?.message || err),
  });

  const sessionString = (client.session as StringSession).save();
  const me = await client.getMe();

  console.log("\n=======================================================");
  console.log(`🎉 Logged in successfully as: ${(me as any).firstName || "Telegram User"} (ID: ${(me as any).id})`);
  console.log("=======================================================\n");

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

  updateOrAppend("TELEGRAM_SESSION", sessionString);
  updateOrAppend("TELEGRAM_TEST_MODE", "false");

  fs.writeFileSync(envPath, envContent.trim() + "\n");
  console.log(`✅ Session saved to .env!`);
  console.log("🚀 You can now start the MCP server using: pnpm start\n");

  rl.close();
  await client.disconnect();
  process.exit(0);
}

main().catch((err) => {
  console.error("\n❌ Login failed:", err?.message || err);
  rl.close();
  process.exit(1);
});
