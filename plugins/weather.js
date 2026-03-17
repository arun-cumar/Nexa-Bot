export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const city = args.join(' ') || 'New York';
    const weather = `🌤️ *WEATHER*\n\nCity: ${city}\nTemp: 25°C\nCondition: Sunny\nHumidity: 65%`;
    await sock.sendMessage(chat, { text: weather }, { quoted: msg });
};
