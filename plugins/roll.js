export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const max = parseInt(args[0]) || 100;
    if (max <= 0) return await sock.sendMessage(chat, { text: "❌ Provide positive number: `.roll 100`" }, { quoted: msg });
    const num = Math.floor(Math.random() * max) + 1;
    await sock.sendMessage(chat, { text: `🎲 *RANDOM NUMBER* (1-${max})\n\n*${num}*` }, { quoted: msg });
};
