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
  console.log("   Telegram Bot MCP - Account Login Helper             ");
  console.log("=======================================================\n");

  const apiIdStr = process.env.TELEGRAM_API_ID;
  const apiHash = process.env.TELEGRAM_API_HASH;

  if (!apiIdStr || !apiHash) {
    console.error("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in .env file.");
    process.exit(1);
  }

  const apiId = parseInt(apiIdStr.trim(), 10);
  const apiHashClean = apiHash.trim();

  const choice = await askQuestion(
    "Select Environment:\n  [1] Production Account (Standard Telegram App)\n  [2] Beta / Test Server Account (Telegram Beta / Test DC)\nChoice (1 or 2, default: 2): "
  );

  const isTestServer = choice.trim() !== "1";

  console.log(`\nConnecting to Telegram ${isTestServer ? "TEST / BETA Server (DC 2)" : "PRODUCTION Server"}...`);

  const client = new TelegramClient(new StringSession(""), apiId, apiHashClean, {
    connectionRetries: 5,
    useIPV6: false,
    testServers: isTestServer,
  });

  await client.start({
    phoneNumber: async () => {
      const phone = await askQuestion(
        isTestServer
          ? "📱 Enter your Beta / Test phone number (e.g. 9996621234 or +...): "
          : "📱 Enter your phone number with country code (e.g. +91XXXXXXXXXX): "
      );
      return phone.trim();
    },
    password: async () => {
      const pw = await askQuestion("🔑 Enter 2FA Password (leave empty & press Enter if none): ");
      return pw.trim();
    },
    phoneCode: async () => {
      const code = await askQuestion(
        isTestServer
          ? "📩 Enter the verification code (usually 22222 or code from Beta app): "
          : "📩 Enter the code received in your Telegram App: "
      );
      return code.trim();
    },
    firstAndLastNames: async () => ["Agent", "Tester"],
    onError: (err) => console.error("⚠️ Login warning:", err?.message || err),
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
  updateOrAppend("TELEGRAM_TEST_MODE", isTestServer ? "true" : "false");

  fs.writeFileSync(envPath, envContent.trim() + "\n");
  console.log(`✅ Session string saved to: ${envPath}`);
  console.log(`✅ TELEGRAM_TEST_MODE set to: ${isTestServer ? "true" : "false"}`);
  console.log("\n🚀 You can now start the MCP server using: pnpm start\n");

  rl.close();
  await client.disconnect();
  process.exit(0);
}

main().catch((err) => {
  console.error("\n❌ Login failed:", err?.message || err);
  rl.close();
  process.exit(1);
});
