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
            .map(f => f.replace('.js', ''));

        const prefix = config.PREFIX;
        const now = new Date();
        const time = now.toLocaleTimeString();
        const date = now.toLocaleDateString();

        const menuText =
`╭━━━〔 *🤖 NEXA-BOT MD MENU* 〕━━━╮
┃
┃  📅 *Date:* ${date}
┃  🕐 *Time:* ${time}
┃  🔖 *Prefix:* [ ${prefix} ]
┃  📦 *Plugins:* ${commands.length}
┃  👤 *Owner:* ${config.OWNER_NAME.join(' & ')}
┃
╰━━━━━━━━━━━━━━━━━━━━━╯

╭━━〔 🛠️ *COMMANDS* 〕━━╮
${commands.map((c, i) => `┃  ${i + 1}. ${prefix}${c}`).join('\n')}
╰━━━━━━━━━━━━━━━━━━━╯

> 🚀 *Powered by Nexa-Bot MD v2.0*`;

        const imagePath = './media/nexa.jpg';
        const imageExists = await fs.access(imagePath).then(() => true).catch(() => false);

        if (imageExists) {
            await sock.sendMessage(chat, {
                image: { url: imagePath },
                caption: menuText
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: menuText }, { quoted: msg });
        }
    } catch (e) {
        console.error('Menu Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to load menu.' }, { quoted: msg });
    }
};
