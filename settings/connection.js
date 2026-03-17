import fs from 'fs'  
import { DisconnectReason } from '@whiskeysockets/baileys'

const connection = async (sock, startNexa, saveCreds) => {

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect } = update;

        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            console.log("❌ Connection Closed. Reason:", reason);

            const shouldReconnect = reason !== DisconnectReason.loggedOut;
            
            if (shouldReconnect) {
                console.log("🔁 Reconnecting...");
                startNexa();
            } else {
                console.log("❌ Logged out. Please delete the session folder and link again.");
            }
        } 
        
        else if (connection === 'open') {
            console.log('\x1b[36m✅ Nexa-Bot MD Connected Successfully!\x1b[0m');
          
            const myNumber = sock.user.id.split(':')[0] + "@s.whatsapp.net";
            const activeMsg = `
╭━━〔 *Nexa-Bot-MD* 〕━━╮
┃🛠️ STATUS: Online
┃👤 OWNER: Arun & Ansad
╰━━━━━━━━━━━━━━━╯`;

            try {
                const imagePath = './media/image.jpg';
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
