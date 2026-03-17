export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.binary hello`" }, { quoted: msg });
    const text = args.join(' ');
    const binary = text.split('').map(c => c.charCodeAt(0).toString(2)).join(' ');
    await sock.sendMessage(chat, { text: `🔢 *BINARY*\n\n${binary}` }, { quoted: msg });
};
