export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const memes = [
        'Why did the developer go broke? He used up all his cache!',
        'How many programmers does it take to change a light bulb? None, that\'s a hardware problem!',
        'Why do Java developers wear glasses? They don\'t see C#',
        'What\'s the object-oriented way to become wealthy? Inheritance!',
        'Why did the programmer quit his job? Because he didn\'t get arrays!'
    ];
    const meme = memes[Math.floor(Math.random() * memes.length)];
    await sock.sendMessage(chat, { text: `😂 *MEME*\n\n${meme}` }, { quoted: msg });
};
