export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const emojis = ['😀', '😂', '😍', '🤔', '😎', '🔥', '💯', '✨', '🎉', '🚀', '💪', '👏'];
    const text = args.join(' ');
    if (!text) return await sock.sendMessage(chat, { text: '❌ Provide text: `.emoji hello`' }, { quoted: msg });
    const emoji = emojis[Math.floor(Math.random() * emojis.length)];
    await sock.sendMessage(chat, { text: `${emoji} ${text} ${emoji}` }, { quoted: msg });
};
