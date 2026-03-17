export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const expr = args.join(' ');
    if (!expr) return await sock.sendMessage(chat, { text: "❌ Usage: `.calc 5+5*2`" }, { quoted: msg });
    try {
        const result = Function('"use strict"; return (' + expr + ')')();
        await sock.sendMessage(chat, { text: `🧮 *${expr}* = *${result}*` }, { quoted: msg });
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Invalid expression' }, { quoted: msg });
    }
};
