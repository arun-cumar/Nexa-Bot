// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import path from 'path';
import config from '../../config.js';
import { menuDesigns } from '../../lib/nexa/menu.js';

export default async (sock, msg, args) => {
    try {
        const from = msg.key.remoteJid;
        const sender = msg.key.participant || from;
        const pushName = msg.pushName || "User";

        // Date
        const date = new Date().toLocaleDateString();

        // Plugins folder path
        const pluginsDir = path.join(process.cwd(), 'plugins');

        // Category folders
        const categories = fs.readdirSync(pluginsDir)
            .filter(folder =>
                fs.lstatSync(path.join(pluginsDir, folder)).isDirectory()
            );

        let commandList = '';
        let totalCommands = 0;

        // Loop categories
        for (const category of categories) {
            const categoryPath = path.join(pluginsDir, category);

            const files = fs.readdirSync(categoryPath)
                .filter(file => file.endsWith('.js') && !file.startsWith('_'));

            if (!files.length) continue;

            commandList += `〔 ${category.toUpperCase()} 〕\n`;

            for (const file of files) {
                const cmd = file.replace('.js', '');
                commandList += `│ ${config.PREFIX}${cmd}\n`;
                totalCommands++;
            }

            commandList += `╰─────────────╯\n\n`;
        }

        // Random design
        const design = menuDesigns[Math.floor(Math.random() * menuDesigns.length)];

        const menuText = design
            .replace('{bot}', config.BOT_NAME)
            .replace('{user}', pushName)
            .replace('{date}', date)
            .replace('{prefix}', config.PREFIX)
            .replace('{commands}', commandList);

        // Send menu with thumbnail
        await sock.sendMessage(from, {
            image: fs.readFileSync(path.join(process.cwd(), 'media', 'nexa.jpg')),
            caption: menuText,
            mentions: [sender]
        }, { quoted: msg });

    } catch (err) {
        console.log("Menu Error:", err);

        await sock.sendMessage(msg.key.remoteJid, {
            text: "❌ Menu error"
        });
    }
};
