export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const uptime = process.uptime();
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const name = sock.user?.name || 'Nexa Bot';
    const jid = sock.user?.id || 'Unknown';
    const stats = `📊 *BOT STATS*\n\n🤖 Name: ${name}\nJID: ${jid}\n⏱️ Uptime: ${hours}h ${minutes}m`;
    await sock.sendMessage(chat, { text: stats }, { quoted: msg });
};
