import { runtime, timeDesigns } from '../../lib/nexa/function.js';
import fs from 'fs';
import path from 'path';

export default async (sock, msg) => {
    try {
        const from = msg.key.remoteJid;

        const uptime = runtime(process.uptime());
        const user = msg.pushName || "User";
        const date = new Date().toLocaleDateString();
        const time = new Date().toLocaleTimeString();

        const imagePath = path.join(process.cwd(), 'media', 'nexa.jpg');

        const design = timeDesigns[Math.floor(Math.random() * timeDesigns.length)];
        
        const timeText = design
            .replace('{user}', user)
            .replace('{uptime}', uptime)
            .replace('{date}', date)
            .replace('{time}', time);

        if (fs.existsSync(imagePath)) {
            await sock.sendMessage(from, {
                image: { url: imagePath }, 
                caption: timeText
            }, { quoted: msg });
        } else {
            await sock.sendMessage(from, { text: timeText }, { quoted: msg });
        }

    } catch (err) {
        console.error("Uptime Error:", err);
    }
};


