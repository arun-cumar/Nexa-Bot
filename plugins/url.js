export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: '❌ Usage: `.url encode|decode <text>`' }, { quoted: msg });
    const op = args[0].toLowerCase();
    const text = args.slice(1).join(' ');
    let result;
    if (op === 'encode') result = encodeURIComponent(text);
    else if (op === 'decode') result = decodeURIComponent(text);
    else return await sock.sendMessage(chat, { text: '❌ Unknown operation' }, { quoted: msg });
    await sock.sendMessage(chat, { text: `🔗 *${op.toUpperCase()}*\n\n${result}` }, { quoted: msg });
};
