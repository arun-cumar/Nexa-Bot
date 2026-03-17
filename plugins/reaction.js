export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const emojis = ['😂', '❤️', '😮', '😢', '🔥', '👏', '🎉', '😍'];
    const emoji = emojis[Math.floor(Math.random() * emojis.length)];
    await sock.sendMessage(chat, { react: { text: emoji, key: msg.key } });
};
