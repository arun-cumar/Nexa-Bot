import fs from 'fs';
import config from '../config.js';

const filterFile = './media/filters.json';

const getFilters = () => {
    if (fs.existsSync(filterFile)) return JSON.parse(fs.readFileSync(filterFile));
    return { words: [], enabled: false };
};

const saveFilters = (data) => {
    fs.writeFileSync(filterFile, JSON.stringify(data, null, 2));
};

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);

    if (!isOwner) {
        return await sock.sendMessage(chat, { text: '❌ Only the *owner* can manage filters.' }, { quoted: msg });
    }

    const filters = getFilters();
    const sub = args[0]?.toLowerCase();

    if (!sub) {
        return await sock.sendMessage(chat, {
            text:
`╭━━〔 🚫 *WORD FILTER* 〕━━╮
┃
┃  Status: ${filters.enabled ? '✅ ON' : '❌ OFF'}
┃  Words: ${filters.words.length}
┃
┃  *Commands:*
┃  .filter on   – Enable filter
┃  .filter off  – Disable filter
┃  .filter add <word>
┃  .filter del <word>
┃  .filter list
┃
╰━━━━━━━━━━━━━━━━━━━╯`
        }, { quoted: msg });
    }

    if (sub === 'on')  { filters.enabled = true;  saveFilters(filters); return await sock.sendMessage(chat, { text: '✅ Word filter *enabled*.' }, { quoted: msg }); }
    if (sub === 'off') { filters.enabled = false; saveFilters(filters); return await sock.sendMessage(chat, { text: '❌ Word filter *disabled*.' }, { quoted: msg }); }

    if (sub === 'add') {
        const word = args[1]?.toLowerCase();
        if (!word) return await sock.sendMessage(chat, { text: '❌ Provide a word: `.filter add <word>`' }, { quoted: msg });
        if (filters.words.includes(word)) return await sock.sendMessage(chat, { text: `⚠️ *${word}* is already in the filter list.` }, { quoted: msg });
        filters.words.push(word);
        saveFilters(filters);
        return await sock.sendMessage(chat, { text: `✅ Added *${word}* to filter list.` }, { quoted: msg });
    }

    if (sub === 'del' || sub === 'remove') {
        const word = args[1]?.toLowerCase();
        if (!word) return await sock.sendMessage(chat, { text: '❌ Provide a word: `.filter del <word>`' }, { quoted: msg });
        filters.words = filters.words.filter(w => w !== word);
        saveFilters(filters);
        return await sock.sendMessage(chat, { text: `✅ Removed *${word}* from filter list.` }, { quoted: msg });
    }

    if (sub === 'list') {
        const list = filters.words.length ? filters.words.map((w, i) => `${i + 1}. ${w}`).join('\n') : 'No filtered words.';
        return await sock.sendMessage(chat, {
            text: `🚫 *Filtered Words:*\n\n${list}`
        }, { quoted: msg });
    }

    await sock.sendMessage(chat, { text: '❌ Unknown sub-command. Use `.filter` for help.' }, { quoted: msg });
};
