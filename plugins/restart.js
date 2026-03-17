import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);

    if (!isOwner) {
        return await sock.sendMessage(chat, { text: '❌ Only the *owner* can restart the bot.' }, { quoted: msg });
    }

    await sock.sendMessage(chat, {
        text: '🔄 *Restarting Nexa-Bot MD...*\n\n✅ Bot will be back in a few seconds!'
    }, { quoted: msg });

    setTimeout(() => process.exit(0), 2000);
};
