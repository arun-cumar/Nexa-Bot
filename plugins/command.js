import { promises as fs } from 'fs';
import path from 'path';
import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    try {
        const pluginsDir = path.join(process.cwd(), 'plugins');
        const files = await fs.readdir(pluginsDir);
        const commands = files
            .filter(f => f.endsWith('.js'))
            .map(f => f.replace('.js', ''))
            .sort();

        const prefix = config.PREFIX;

        const categories = {
            '🤖 Bot': ['alive', 'menu', 'command', 'ping', 'restart'],
            '🎨 Media': ['sticker', 'take', 'pdf'],
            '✨ Fun': ['fancy', 'game'],
            '📥 Downloads': ['downloader'],
            '👥 Group': ['group', 'manage', 'mention', 'welcome', 'filter'],
        };

        let result = `╭━━〔 📋 *COMMAND LIST* 〕━━╮\n┃\n`;
        const categorized = new Set();

        for (const [cat, cmds] of Object.entries(categories)) {
            const found = cmds.filter(c => commands.includes(c));
            if (!found.length) continue;
            result += `┃  *${cat}*\n`;
            found.forEach(c => { result += `┃   • ${prefix}${c}\n`; categorized.add(c); });
            result += `┃\n`;
        }

        const others = commands.filter(c => !categorized.has(c));
        if (others.length) {
            result += `┃  *🔧 Other*\n`;
            others.forEach(c => { result += `┃   • ${prefix}${c}\n`; });
            result += `┃\n`;
        }

        result += `╰━━━━━━━━━━━━━━━━━━━━━╯\n\n> 📦 Total: ${commands.length} commands`;

        await sock.sendMessage(chat, { text: result }, { quoted: msg });
    } catch (e) {
        console.error('Command Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to load commands.' }, { quoted: msg });
    }
};
