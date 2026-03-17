export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;

    if (!chat.endsWith('@g.us')) {
        return await sock.sendMessage(chat, { text: '❌ This command works in *groups only*.' }, { quoted: msg });
    }

    try {
        const meta = await sock.groupMetadata(chat);
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        const members = meta.participants.length;
        const adminCount = admins.length;

        const created = new Date(meta.creation * 1000).toLocaleDateString();

        const groupInfo =
`╭━━〔 👥 *GROUP INFO* 〕━━╮
┃
┃  📛 *Name:* ${meta.subject}
┃  📝 *Desc:* ${meta.desc ? meta.desc.slice(0, 60) + (meta.desc.length > 60 ? '...' : '') : 'No description'}
┃  👤 *Members:* ${members}
┃  🛡️ *Admins:* ${adminCount}
┃  📅 *Created:* ${created}
┃  🔗 *Group ID:* ${chat.split('@')[0]}
┃
╰━━━━━━━━━━━━━━━━━━━━━╯`;

        const pp = await sock.profilePictureUrl(chat, 'image').catch(() => null);

        if (pp) {
            await sock.sendMessage(chat, {
                image: { url: pp },
                caption: groupInfo
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: groupInfo }, { quoted: msg });
        }
    } catch (e) {
        console.error('Group Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to fetch group info.' }, { quoted: msg });
    }
};
