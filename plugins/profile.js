export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    try {
        const profile = await sock.fetchBusinessProfile(sender) || {};
        const pp = await sock.profilePictureUrl(sender, 'image').catch(() => null);
        const name = profile.name || sender.split('@')[0];
        const bio = profile.description || 'No bio';
        const info = `👤 *PROFILE*\n\nName: ${name}\nBio: ${bio}\nJID: ${sender}`;
        if (pp) {
            await sock.sendMessage(chat, { image: { url: pp }, caption: info }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: info }, { quoted: msg });
        }
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Failed to fetch profile' }, { quoted: msg });
    }
};
