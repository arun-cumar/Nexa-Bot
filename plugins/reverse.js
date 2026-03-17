export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.reverse hello`" }, { quoted: msg });
    const text = args.join(' ');
    const reversed = text.split('').reverse().join('');
    await sock.sendMessage(chat, { text: `🔄 *REVERSE*\n\n${reversed}` }, { quoted: msg });
};
