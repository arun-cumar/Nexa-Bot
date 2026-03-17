export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    await sock.sendMessage(chat, { text: '✅ *BOT IS WORKING PERFECTLY!*\n\nTest passed 🎉' }, { quoted: msg });
};
