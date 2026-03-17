export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const length = parseInt(args[0]) || 12;
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < length; i++) password += chars[Math.floor(Math.random() * chars.length)];
    await sock.sendMessage(chat, { text: `🔐 *STRONG PASSWORD*\n\n${password}` }, { quoted: msg });
};
