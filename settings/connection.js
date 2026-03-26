// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import config from "../config.js";
import { DisconnectReason } from '@whiskeysockets/baileys';

const delay = (ms) => new Promise(res => setTimeout(res, ms));

const connection = async (sock, startNexa, saveCreds) => {

    sock.ev.on('connection.update', async (update) => {
        try {
            const { connection, lastDisconnect } = update;

            if (connection === 'close') {
                const reason = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = reason !== DisconnectReason.loggedOut;

                console.log(`❌ Connection Closed. Reason: ${reason}`);

                if (shouldReconnect) {
                    console.log("🔁 Reconnecting in 5 seconds...");
                    await delay(5000);
                    startNexa();
                } else {
                    console.log("🚪 Logged Out. Scan QR again.");
                }
            }

            else if (connection === 'connecting') {
                console.log("🔄 Connecting to WhatsApp...");
            }

            else if (connection === 'open') {
                console.log('\x1b[36m✅ Nexa-Bot MD Connected Successfully!\x1b[0m');

                const myNumber = sock.user.id.split(':')[0] + "@s.whatsapp.net";

                const activeMsg = `
╭━━〔 ${config.BOT_NAME} 〕━━╮
┃ 🛠️ STATUS: Online
┃ 👤 OWNER: ${config.OWNER_NAME}
┃ 📞 CONTACT: ${config.OWNER_NUMBER}
┃ ⚡ PREFIX: ${config.PREFIX}
┃ 📝 DESC: ${config.DESCRIPTION}
╰━━━━━━━━━━━━━━━╯`;

                try {
                    const imagePath = './media/nexa.jpg';

                    if (fs.existsSync(imagePath)) {
                        await sock.sendMessage(myNumber, {
                            image: fs.readFileSync(imagePath),
                            caption: activeMsg
                        });
                    } else {
                        await sock.sendMessage(myNumber, { text: activeMsg });
                    }
                } catch (err) {
                    console.log("❌ Login Notification Error:", err.message);
                }
            }

        } catch (err) {
            console.log("❌ Connection Handler Error:", err);
        }
    });

    sock.ev.on('creds.update', saveCreds);
};

export default connection;
