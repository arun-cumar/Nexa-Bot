export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: '❌ Provide text: `.slug hello world`' }, { quoted: msg });
    const text = args.join(' ').toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
    await sock.sendMessage(chat, { text: `🔤 *SLUG*\n\n${text}` }, { quoted: msg });
};
