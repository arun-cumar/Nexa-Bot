export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const song = args.join(' ');
    if (!song) return await sock.sendMessage(chat, { text: '❌ Provide song: `.lyrics shape of you`' }, { quoted: msg });
    const lyrics = `🎵 *${song.toUpperCase()}*\n\n[Lyrics would require API access]`;
    await sock.sendMessage(chat, { text: lyrics }, { quoted: msg });
};
