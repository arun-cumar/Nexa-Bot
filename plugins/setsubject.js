import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    if (!chat.endsWith('@g.us')) return await sock.sendMessage(chat, { text: '❌ Group only' }, { quoted: msg });
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);
    if (!args.length) return await sock.sendMessage(chat, { text: '❌ Provide name: `.setsubject <name>`' }, { quoted: msg });
    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        if (!admins.includes(sender) && !isOwner) return await sock.sendMessage(chat, { text: '❌ Admin only' }, { quoted: msg });
        const name = args.join(' ');
        await sock.groupUpdateSubject(chat, name);
        await sock.sendMessage(chat, { text: '✅ Group name updated!' }, { quoted: msg });
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Error: ' + e.message }, { quoted: msg });
    }
};
