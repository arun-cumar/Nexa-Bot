import fs from 'fs';
import config from '../config.js';

const autoFile = './media/autoreply.json';
const getAuto = () => fs.existsSync(autoFile) ? JSON.parse(fs.readFileSync(autoFile)) : {};
const saveAuto = (a) => fs.writeFileSync(autoFile, JSON.stringify(a, null, 2));

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);
    if (!isOwner) return await sock.sendMessage(chat, { text: '❌ Owner only' }, { quoted: msg });
    const sub = args[0]?.toLowerCase();
    const auto = getAuto();
    if (sub === 'add') {
        const trigger = args[1];
        const response = args.slice(2).join(' ');
        if (!trigger || !response) return await sock.sendMessage(chat, { text: '❌ Usage: `.autoreply add trigger response`' }, { quoted: msg });
        auto[trigger.toLowerCase()] = response;
        saveAuto(auto);
        await sock.sendMessage(chat, { text: `✅ Autoreply added` }, { quoted: msg });
    } else if (sub === 'del') {
        const trigger = args[1]?.toLowerCase();
        if (!trigger) return await sock.sendMessage(chat, { text: '❌ Usage: `.autoreply del trigger`' }, { quoted: msg });
        delete auto[trigger];
        saveAuto(auto);
        await sock.sendMessage(chat, { text: `✅ Autoreply deleted` }, { quoted: msg });
    } else {
        await sock.sendMessage(chat, { text: `❌ Usage: .autoreply add|del <trigger> [response]` }, { quoted: msg });
    }
};
