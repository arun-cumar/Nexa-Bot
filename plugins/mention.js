import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;

    if (!chat.endsWith('@g.us')) {
        return await sock.sendMessage(chat, { text: '❌ This command works in *groups only*.' }, { quoted: msg });
    }

    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        const isAdmin = admins.includes(sender);
        const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);

        if (!isAdmin && !isOwner) {
            return await sock.sendMessage(chat, { text: '❌ Only *admins* can use this command.' }, { quoted: msg });
        }

        const members = meta.participants.map(p => p.id);
        const message = args.join(' ') || '👋 Hello everyone!';

        const text = `📢 *Mention All*\n\n${message}\n\n` +
            members.map(m => `@${m.split('@')[0]}`).join(' ');

        await sock.sendMessage(chat, {
            text,
            mentions: members
        }, { quoted: msg });
    } catch (e) {
        console.error('Mention Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to mention members.' }, { quoted: msg });
    }
};
