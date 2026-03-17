import fs from 'fs';
import config from '../config.js';

const warnFile = './media/warns.json';
const getWarns = () => fs.existsSync(warnFile) ? JSON.parse(fs.readFileSync(warnFile)) : {};
const saveWarns = (w) => fs.writeFileSync(warnFile, JSON.stringify(w, null, 2));

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    if (!chat.endsWith('@g.us')) return await sock.sendMessage(chat, { text: '❌ Group only' }, { quoted: msg });
    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        if (!admins.includes(sender) && !config.OWNER_NUMBER.includes(sender.split('@')[0])) return await sock.sendMessage(chat, { text: '❌ Admin only' }, { quoted: msg });
        const mentioned = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid?.[0];
        if (!mentioned) return await sock.sendMessage(chat, { text: '❌ Mention a user' }, { quoted: msg });
        const warns = getWarns();
        if (!warns[chat]) warns[chat] = {};
        warns[chat][mentioned] = (warns[chat][mentioned] || 0) + 1;
        saveWarns(warns);
        const count = warns[chat][mentioned];
        await sock.sendMessage(chat, { text: `⚠️ @${mentioned.split('@')[0]} has been warned (${count}/3)`, mentions: [mentioned] }, { quoted: msg });
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Error' }, { quoted: msg });
    }
};
