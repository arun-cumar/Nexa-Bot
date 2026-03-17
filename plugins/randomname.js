export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const names = ['Alex', 'Jordan', 'Casey', 'Morgan', 'Taylor', 'Riley', 'Cameron', 'Avery', 'Quinn', 'Sydney', 'Blake', 'Dakota'];
    const name = names[Math.floor(Math.random() * names.length)];
    await sock.sendMessage(chat, { text: `👤 *RANDOM NAME*\n\n${name}` }, { quoted: msg });
};
