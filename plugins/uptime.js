import os from 'os';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const uptime = os.uptime();
    const days = Math.floor(uptime / 86400);
    const hours = Math.floor((uptime % 86400) / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    await sock.sendMessage(chat, {
        text: `⏱️ *SYSTEM UPTIME*\n\n${days}d ${hours}h ${minutes}m`
    }, { quoted: msg });
};
