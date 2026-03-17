export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const cmd = args[0]?.toLowerCase();
    const helps = {
        menu: 'Show all commands with image',
        alive: 'Check bot status and uptime',
        sticker: 'Convert image to sticker',
        help: 'Get command help'
    };
    if (cmd && helps[cmd]) {
        await sock.sendMessage(chat, { text: `📖 *${cmd.toUpperCase()}*\n\n${helps[cmd]}` }, { quoted: msg });
    } else {
        await sock.sendMessage(chat, { text: '❌ Usage: `.help <command>`' }, { quoted: msg });
    }
};
