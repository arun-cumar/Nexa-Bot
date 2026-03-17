export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const text = args.join(' ');
    if (!text) return await sock.sendMessage(chat, { text: '❌ Provide text: `.flip hello`' }, { quoted: msg });
    const flipped = text.split('').reverse().map(c => {
        const flipMap = { 'b': 'd', 'd': 'b', 'p': 'q', 'q': 'p', 'm': 'w', 'w': 'm' };
        return flipMap[c] || c;
    }).join('');
    await sock.sendMessage(chat, { text: `🔄 *FLIPPED*\n\n${flipped}` }, { quoted: msg });
};
