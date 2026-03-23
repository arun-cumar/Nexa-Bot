// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs'  
import { DisconnectReason } from '@whiskeysockets/baileys'
const connection = async (sock, startNexa, saveCreds) => {

   sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect } = update;
        
        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = reason !== DisconnectReason.loggedOut;
            
            console.log(`❌ Connection Closed. Reason: ${reason}`);
            
            if (shouldReconnect) {
                console.log("🔁 Reconnecting...");
                startNexa();
            }
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
    });

    sock.ev.on('creds.update', saveCreds);
};

export default connection;
