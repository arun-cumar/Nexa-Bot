export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: '❌ Provide birthdate: `.age 2000-05-15`' }, { quoted: msg });
    try {
        const birthDate = new Date(args[0]);
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        if (today.getMonth() < birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate())) age--;
        await sock.sendMessage(chat, { text: `🎂 *AGE CALCULATOR*\n\nYour age: ${age} years` }, { quoted: msg });
    } catch {
        await sock.sendMessage(chat, { text: '❌ Invalid date format (use YYYY-MM-DD)' }, { quoted: msg });
    }
};
