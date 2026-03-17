import crypto from 'crypto';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const text = args.join(' ');
    if (!text) return await sock.sendMessage(chat, { text: '❌ Provide text: `.hasher hello`' }, { quoted: msg });
    const md5 = crypto.createHash('md5').update(text).digest('hex');
    const sha1 = crypto.createHash('sha1').update(text).digest('hex');
    const sha256 = crypto.createHash('sha256').update(text).digest('hex');
    await sock.sendMessage(chat, {
        text: `🔐 *HASHES*\n\nMD5: ${md5}\nSHA1: ${sha1}\nSHA256: ${sha256}`
    }, { quoted: msg });
};
