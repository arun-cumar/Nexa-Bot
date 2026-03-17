export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const secs = parseInt(args[0]) || 60;
    if (secs <= 0 || secs > 3600) return await sock.sendMessage(chat, { text: "❌ Set 1-3600 seconds" }, { quoted: msg });
    const { key } = await sock.sendMessage(chat, { text: `⏱️ *Timer: ${secs}s*` }, { quoted: msg });
    let remaining = secs;
    const interval = setInterval(async () => {
        remaining--;
        if (remaining % 10 === 0 || remaining <= 5) {
            await sock.sendMessage(chat, { text: `⏱️ *${remaining}s remaining*`, edit: key });
        }
        if (remaining === 0) {
            clearInterval(interval);
            await sock.sendMessage(chat, { text: `⏰ *TIME'S UP!*`, edit: key });
        }
    }, 1000);
};
