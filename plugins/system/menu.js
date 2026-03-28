// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import path from 'path';
import config from '../../../config.js';
import { menuDesigns } from '../../../lib/nexa/menu.js';

export default async (sock, msg, args) => {
    try {
        const from = msg.key.remoteJid;
        const pushName = msg.pushName || "User";

        // Time & Date
        const date = new Date().toLocaleDateString();
        const time = new Date().toLocaleTimeString();

        const pluginsDir = path.join(process.cwd(), 'plugins');
        
        const categories = fs.readdirSync(pluginsDir).filter(file => {
            return fs.statSync(path.join(pluginsDir, file)).isDirectory();
        });

        let allCommandsText = '';
        let totalCommands = 0;

        categories.forEach(category => {
            const categoryPath = path.join(pluginsDir, category);
            const files = fs.readdirSync(categoryPath).filter(file => file.endsWith('.js'));

            if (files.length > 0) {
                allCommandsText += `\n*──『 ${category.toUpperCase()} 』──*\n`;
                files.forEach(file => {
                    const cmd = file.replace('.js', '');
                    allCommandsText += `  ◦ ${config.PREFIX}${cmd}\n`;
                    totalCommands++;
                });
            }
        });

        const randomDesign = menuDesigns[Math.floor(Math.random() * menuDesigns.length)];

        const menuText = randomDesign
            .replace(/{bot}/g, config.BOT_NAME || "Nexa-Bot")
            .replace(/{user}/g, pushName)
            .replace(/{date}/g, date)
            .replace(/{prefix}/g, config.PREFIX)
            .replace(/{commands}/g, allCommandsText);

        const imagePath = path.join(process.cwd(), 'media', 'nexa.jpg');
        let imageBuffer;
        if (fs.existsSync(imagePath)) {
            imageBuffer = fs.readFileSync(imagePath);
        }

        await sock.sendMessage(from, {
            text: menuText,
            contextInfo: {
                externalAdReply: {
                    title: config.BOT_NAME || "Nexa-Bot",
                    body: "Nexa Multi-Device Bot",
                    mediaType: 1,
                    sourceUrl: "https://whatsapp.com/channel/0029VbB59W9GehENxhoI5l24",
                    thumbnail: imageBuffer 
                }
            }
        }, { quoted: msg });

    } catch (err) {
        console.error("Menu Error:", err);
        await sock.sendMessage(msg.key.remoteJid, { text: "❌ error." });
    }
};
