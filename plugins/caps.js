export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.caps hello world`" }, { quoted: msg });
    const text = args.join(' ');
    const caps = text.toUpperCase();
    const low = text.toLowerCase();
    const mixed = text.split('').map((c, i) => i % 2 === 0 ? c.toUpperCase() : c.toLowerCase()).join('');
    await sock.sendMessage(chat, {
        text: `🔤 *TEXT STYLES*\n\n*UPPERCASE:* ${caps}\n*lowercase:* ${low}\n*MiXeD:* ${mixed}`
    }, { quoted: msg });
};
