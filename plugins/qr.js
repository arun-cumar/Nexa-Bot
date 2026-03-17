import QRCode from 'qrcode';
import path from 'path';
import fs from 'fs';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.qr hello`" }, { quoted: msg });
    const text = args.join(' ');
    await sock.sendMessage(chat, { react: { text: '📱', key: msg.key } });
    try {
        const outPath = path.join('/tmp', `qr_${Date.now()}.png`);
        await QRCode.toFile(outPath, text);
        await sock.sendMessage(chat, { image: fs.readFileSync(outPath), caption: `📱 *QR Code*\n\n${text}` }, { quoted: msg });
        fs.unlinkSync(outPath);
    } catch (e) {
        await sock.sendMessage(chat, { text: '❌ Failed to generate QR code' }, { quoted: msg });
    }
};
