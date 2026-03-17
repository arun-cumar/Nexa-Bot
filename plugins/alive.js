import fs from 'fs';
import config from '../config.js';
import os from 'os';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    try {
        await sock.sendMessage(chat, { react: { text: '💚', key: msg.key } });

        const uptime = process.uptime();
        const hrs  = Math.floor(uptime / 3600);
        const mins = Math.floor((uptime % 3600) / 60);
        const secs = Math.floor(uptime % 60);

        const ramTotal = (os.totalmem() / 1024 / 1024).toFixed(0);
        const ramFree  = (os.freemem()  / 1024 / 1024).toFixed(0);
        const ramUsed  = (ramTotal - ramFree).toFixed(0);

        const aliveText =
`╭━━〔 *✅ NEXA-BOT ALIVE* 〕━━╮
┃
┃  🤖 *Bot:* ${config.BOT_NAME}
┃  👤 *Owner:* ${config.OWNER_NAME.join(' & ')}
┃  🔖 *Prefix:* [ ${config.PREFIX} ]
┃  🌐 *Status:* Online
┃
┃  ⏱️ *Uptime:* ${hrs}h ${mins}m ${secs}s
┃  💾 *RAM Used:* ${ramUsed} MB / ${ramTotal} MB
┃  📱 *Platform:* ${os.platform()} ${os.arch()}
┃
╰━━━━━━━━━━━━━━━━━━━━━╯

> 🚀 Nexa-Bot MD v2.0 is running!`;

        const imagePath = './media/nexa.jpg';

        if (fs.existsSync(imagePath)) {
            await sock.sendMessage(chat, {
                image: fs.readFileSync(imagePath),
                caption: aliveText
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: aliveText }, { quoted: msg });
        }
    } catch (e) {
        console.error('Alive Error:', e);
        await sock.sendMessage(chat, { text: '❌ Error checking alive status.' });
    }
};
