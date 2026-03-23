// © 2026 arun•°Cumar. All Rights Reserved.
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
import { handlePairing } from "./settings/pairing.js";
import { handleOwnerEvents } from "./settings/community.js";
import connectionHandler from "./settings/connection.js";
import messageHandler from "./message.js";
import config from "./config.js"; 

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

       await handlePairing(sock);
    handleOwnerEvents(sock);

    connectionHandler(sock, startNexa, saveCreds);

    sock.ev.on("messages.upsert", async (chatUpdate) => {
        await messageHandler(sock, chatUpdate);
    });
}

startNexa();
