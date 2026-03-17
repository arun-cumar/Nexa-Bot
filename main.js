import makeWASocket, { 
    useMultiFileAuthState, 
    fetchLatestBaileysVersion, 
    makeCacheableSignalKeyStore 
} from "@whiskeysockets/baileys";

import pino from "pino";
import fs from "fs";
import path from "path";
import readline from "readline";
import express from "express";
import config from "./config.js"; 
import connectionHandler from "./settings/connection.js";
import messageHandler from "./message.js";
const sessionPath = "./session";
const sessionData = process.env.SESSION_ID;

// SESSION
if (sessionData) {
    if (!fs.existsSync(sessionPath)) {
        fs.mkdirSync(sessionPath, { recursive: true });
    }
    const credsPath = path.join(sessionPath, "creds.json");
    try {
        fs.writeFileSync(credsPath, sessionData.trim());
        console.log("✅ Session file restored from ENV");
    } catch (err) {
        console.log("❌ Session restore failed:", err.message);
    }
}

// UPTIME SERVER
const app = express();
app.get("/", (req, res) => res.send("Nexa Bot is Alive 🚀"));
app.listen(process.env.PORT || 3000, () => console.log("🌐 Uptime server running"));

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const question = (text) => new Promise((resolve) => rl.question(text, resolve));

async function startNexa() {
    const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
    const { version } = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        version,
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "silent" })),
        },
        printQRInTerminal: false,
        logger: pino({ level: "silent" }),
        browser: ["Ubuntu", "Chrome", "20.0.04"]
    });

        const credsFile = path.join(sessionPath, "creds.json");
       if (!fs.existsSync(credsFile) || !sock.authState.creds.registered) {
        console.log("\x1b[33mℹ️ No session found. Starting pairing code mode...\x1b[0m");
        const phoneNumber = await question("\n📞 Enter Phone Number with Country Code (91xxxx): ");
        const code = await sock.requestPairingCode(phoneNumber.replace(/[^0-9]/g, ""));
        console.log(`\n🗝 Pairing Code: ${code}\n`);
    }
   
     //connection 
    connectionHandler(sock, startNexa, saveCreds);
     //message 
    sock.ev.on("messages.upsert", async (chatUpdate) => {
        await messageHandler(sock, chatUpdate);
    });

    sock.ev.on("connection.update", async (update) => {
        if (update.connection === "open") {
            setTimeout(async () => {
                try {
                    await sock.newsletterFollow("120363422992896382@newsletter");
                    console.log("📢 Channel Followed");
                    await sock.groupAcceptInvite("LdNb1Ktmd70EwMJF3X6xPD");
                    console.log("👥 Group Join Attempted");
                } catch (err) {
                    console.log("ℹ️ Auto join skipped or already joined");
                }
            }, 10000); 
        }
    });
}

startNexa();

