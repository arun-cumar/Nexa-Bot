import { downloadContentFromMessage } from '@whiskeysockets/baileys';
import { uploadToCatbox } from '../lib/url.js'; 

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;
  
    const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage || msg.message;

    const mimeType = quoted.imageMessage ? 'image' : 
                     quoted.videoMessage ? 'video' : 
                     quoted.audioMessage ? 'audio' : 
                     quoted.documentMessage ? 'document' : null;

    if (!mimeType) {
        return sock.sendMessage(from, { text: '❌ *Reply to a media file!*' }, { quoted: msg });
    }

    try {
        await sock.sendMessage(from, { react: { text: "🔗", key: msg.key } });

        const message = quoted.imageMessage || quoted.videoMessage || quoted.audioMessage || quoted.documentMessage;
        const stream = await downloadContentFromMessage(message, mimeType);
        let buffer = Buffer.from([]);
        for await (const chunk of stream) {
            buffer = Buffer.concat([buffer, chunk]);
        }

        const fileName = `asura_${Date.now()}.${mimeType === 'image' ? 'jpg' : 'mp4'}`;
        const url = await uploadToCatbox(buffer, fileName);

        const responseText = `*✅ Uploaded Successfully!*\n\n🔗 *URL:* ${url}\n📂 *Type:* ${mimeType.toUpperCase()}`;

        await sock.sendMessage(from, {
            text: responseText,
            contextInfo: {
                externalAdReply: {
                    title: "Nexa MEDIA UPLOADER",
                    body: "File converted to permanent link",
                    thumbnailUrl: "http://codeskulptor-demos.commondatastorage.googleapis.com/GalaxyInvaders/back03.jpg",
                    sourceUrl: url,
                    renderLargerThumbnail: true
                }
            }
        }, { quoted: msg });

    } catch (e) {
        console.error('URL Command Error:', e);
        await sock.sendMessage(from, { text: "❌ *Upload failed!*" });
    }
};
