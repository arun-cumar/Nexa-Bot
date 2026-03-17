export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const time = parseInt(args[0]) || 60;
    const text = args.slice(1).join(' ') || 'Reminder!';
    await sock.sendMessage(chat, { text: `⏰ Reminder set for ${time} seconds` }, { quoted: msg });
    setTimeout(() => {
        sock.sendMessage(chat, { text: `🔔 *REMINDER*\n\n${text}` });
    }, time * 1000);
};
