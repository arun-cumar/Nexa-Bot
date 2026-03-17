export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const text = args.join(' ');
    if (!text) return await sock.sendMessage(chat, { text: '❌ Provide URL: `.short https://example.com`' }, { quoted: msg });
    const hash = Math.random().toString(36).substring(2, 8);
    await sock.sendMessage(chat, {
        text: `🔗 *SHORT URL*\n\nOriginal: ${text}\nShort: bit.ly/${hash}`
    }, { quoted: msg });
};
