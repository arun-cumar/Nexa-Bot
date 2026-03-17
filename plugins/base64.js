export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sub = args[0]?.toLowerCase();
    if (sub === 'encode') {
        const text = args.slice(1).join(' ');
        if (!text) return await sock.sendMessage(chat, { text: "❌ Usage: `.base64 encode <text>`" }, { quoted: msg });
        const encoded = Buffer.from(text).toString('base64');
        await sock.sendMessage(chat, { text: `🔐 *ENCODED*\n\n${encoded}` }, { quoted: msg });
    } else if (sub === 'decode') {
        const text = args.slice(1).join('');
        if (!text) return await sock.sendMessage(chat, { text: "❌ Usage: `.base64 decode <text>`" }, { quoted: msg });
        try {
            const decoded = Buffer.from(text, 'base64').toString();
            await sock.sendMessage(chat, { text: `🔓 *DECODED*\n\n${decoded}` }, { quoted: msg });
        } catch {
            await sock.sendMessage(chat, { text: '❌ Invalid base64' }, { quoted: msg });
        }
    } else {
        await sock.sendMessage(chat, { text: "❌ Usage: `.base64 encode|decode <text>`" }, { quoted: msg });
    }
};
