export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.echo hello`" }, { quoted: msg });
    const text = args.join(' ');
    await sock.sendMessage(chat, { text: `🔊 *ECHO*\n\n${text}\n${text}` }, { quoted: msg });
};
