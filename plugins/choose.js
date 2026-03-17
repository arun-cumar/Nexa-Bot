export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (args.length < 2) return await sock.sendMessage(chat, { text: "❌ Usage: `.choose option1 option2 option3`" }, { quoted: msg });
    const chosen = args[Math.floor(Math.random() * args.length)];
    await sock.sendMessage(chat, { text: `🎯 *I CHOOSE*\n\n*${chosen}*` }, { quoted: msg });
};
