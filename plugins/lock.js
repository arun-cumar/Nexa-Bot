import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    if (!chat.endsWith('@g.us')) return await sock.sendMessage(chat, { text: '❌ Group only' }, { quoted: msg });
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);
    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        if (!admins.includes(sender) && !isOwner) return await sock.sendMessage(chat, { text: '❌ Admin only' }, { quoted: msg });
        const sub = args[0]?.toLowerCase();
        if (sub === 'on') {
            await sock.groupSettingUpdate(chat, 'locked');
            await sock.sendMessage(chat, { text: '🔒 Group is now *locked* (only admins can edit)' }, { quoted: msg });
        } else if (sub === 'off') {
            await sock.groupSettingUpdate(chat, 'unlocked');
            await sock.sendMessage(chat, { text: '🔓 Group is now *unlocked*' }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: '❌ Usage: `.lock on|off`' }, { quoted: msg });
        }
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Error' }, { quoted: msg });
    }
};
