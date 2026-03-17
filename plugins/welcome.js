import config from '../config.js';
import { getToggles, saveToggles } from '../lib/toggles.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;

    if (!chat.endsWith('@g.us')) {
        return await sock.sendMessage(chat, { text: '❌ This command works in *groups only*.' }, { quoted: msg });
    }

    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);
    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        const isAdmin = admins.includes(sender);

        if (!isAdmin && !isOwner) {
            return await sock.sendMessage(chat, { text: '❌ Only *admins* can change welcome settings.' }, { quoted: msg });
        }
    } catch {}

    const sub = args[0]?.toLowerCase();
    const toggles = getToggles();

    if (!toggles.welcome) toggles.welcome = {};

    if (sub === 'on') {
        toggles.welcome[chat] = true;
        saveToggles(toggles);
        return await sock.sendMessage(chat, {
            text: '✅ *Welcome messages enabled* for this group!\n\nNew members will be greeted automatically.'
        }, { quoted: msg });
    }

    if (sub === 'off') {
        toggles.welcome[chat] = false;
        saveToggles(toggles);
        return await sock.sendMessage(chat, {
            text: '❌ *Welcome messages disabled* for this group.'
        }, { quoted: msg });
    }

    const status = toggles.welcome[chat] ? '✅ ON' : '❌ OFF';
    await sock.sendMessage(chat, {
        text:
`╭━━〔 👋 *WELCOME* 〕━━╮
┃
┃  Status: ${status}
┃
┃  *Commands:*
┃  .welcome on  – Enable
┃  .welcome off – Disable
┃
╰━━━━━━━━━━━━━━━━━╯`
    }, { quoted: msg });
};
