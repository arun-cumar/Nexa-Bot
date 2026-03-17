import { downloadMediaMessage } from '@whiskeysockets/baileys';
import sharp from 'sharp';
import fs from 'fs';
import path from 'path';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    try {
        const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;
        const isImage = quoted?.imageMessage || msg.message?.imageMessage;

        if (!isImage) {
            return await sock.sendMessage(chat, {
                text: '❌ Please reply to an *image* to convert it to a sticker.\n\nUsage: Reply to image with *.sticker*'
            }, { quoted: msg });
        }

        await sock.sendMessage(chat, { react: { text: '🎨', key: msg.key } });

        const msgToDownload = quoted?.imageMessage
            ? { message: quoted, key: { ...msg.key, id: msg.message.extendedTextMessage.contextInfo.stanzaId } }
            : msg;

        const buffer = await downloadMediaMessage(
            quoted?.imageMessage ? { message: { imageMessage: quoted.imageMessage }, key: msg.key } : msg,
            'buffer',
            {}
        );

        const webpBuffer = await sharp(buffer)
            .resize(512, 512, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .webp()
            .toBuffer();

        await sock.sendMessage(chat, { sticker: webpBuffer }, { quoted: msg });
    } catch (e) {
        console.error('Sticker Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to create sticker. Please try again.' }, { quoted: msg });
    }
};
