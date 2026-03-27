import fs from 'fs';
import config from '../config.js';
import os from 'os';
import { aliveStyles } from '../lib/alive.js'; 

export default async (sock, msg, args) => {
    const chat = msg.key.remoteJid;
    try {
        await sock.sendMessage(chat, { react: { text: '🩸', key: msg.key } });

        // Uptime & RAM Calculation
        const uptimeSeconds = process.uptime();
        const hrs = Math.floor(uptimeSeconds / 3600);
        const mins = Math.floor((uptimeSeconds % 3600) / 60);
        const uptime = `${hrs}h ${mins}m`;

        const ram = `${(os.totalmem() - os.freemem()) / 1024 / 1024 | 0}MB / ${os.totalmem() / 1024 / 1024 | 0}MB`;


        const styleData = {
            botName: config.BOT_NAME,
            owner: config.OWNER_NAME[0],
            prefix: config.PREFIX,
            uptime: uptime,
            ram: ram,
            platform: os.platform()
        };

        const aliveText = aliveStyles(styleData);

        const imagePath = './media/nexa.jpg';
        if (fs.existsSync(imagePath)) {
            await sock.sendMessage(chat, {
                image: fs.readFileSync(imagePath),
                caption: aliveText + "\n\n> 🚀 Nexa-Bot MD v2.0"
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: aliveText }, { quoted: msg });
        }
    } catch (e) {
        console.error('Alive Error:', e);
    }
};
