import makeWASocket, { 
    useMultiFileAuthState, 
    DisconnectReason, 
    fetchLatestBaileysVersion, 
    makeCacheableSignalKeyStore 
} from "@whiskeysockets/baileys";
import pino from "pino";
import fs from "fs";
import path from "path";
import { pathToFileURL } from 'url';
import readline from "readline";
import express from "express";
import config from "./config.js";
import connectionHandler from "./settings/connection.js";
import messageHandler from "./message.js";

const sessionPath = './session';
const sessionData = process.env.SESSION_ID;
//SESSION_ID MANAGE
if (sessionData) {
    if (!fs.existsSync(sessionPath)) {
        fs.mkdirSync(sessionPath, { recursive: true });
    }
    const credsPath = path.join(sessionPath, 'creds.json');
    
    try {
        fs.writeFileSync(credsPath, sessionData.trim());
        console.log("✅ Session file updated from Environment Variable");
    } catch (error) {
        console.error("❌ Error restoring session:", error.message);
    }
}

// --- 2. UPTIME SERVER (For Render/Koyeb) ---
const app = express();
app.get('/', (req, res) => res.send('Nexa-Bot MD is Alive! '));
app.listen(process.env.PORT || 3000);

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const question = (text) => new Promise((resolve) => rl.question(text, resolve));
async function startNexa() {
    const { state, saveCreds } = await useMultiFileAuthState('./session');

        const sock = makeWASocket({
        auth: state,
        printQRInTerminal: !process.argv.includes('--pairing-code'),
        browser: ["Ubuntu", "Chrome", "20.0.04"], 
        logger: pino({ level: 'silent' }) 
    });

    if (!sock.authState.creds.registered && process.argv.includes('--pairing-code')) {
        const phoneNumber = await question('\n📞 Enter your Phone Number: ');
const code = await sock.requestPairingCode(phoneNumber.replace(/[^0-9]/g, ''));
console.log(`\x1b[32m\nYOUR 🗝 PAIRING CODE: \x1b[1m${code}\x1b[0m\n`);
rl.close(); 
  }

    connectionHandler(sock, startNexa, saveCreds);
    
    sock.ev.on('messages.upsert', async (chatUpdate) => {
        await messageHandler(sock, chatUpdate);
    });
}

startNexa();
