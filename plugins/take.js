import { downloadMediaMessage } from '@whiskeysockets/baileys';
import sharp from 'sharp';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    try {
        const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;

        if (!quoted) {
            return await sock.sendMessage(chat, {
                text: '❌ Reply to an *image or sticker* to take/steal it.\n\nUsage: Reply with *.take*'
            }, { quoted: msg });
        }

        const isStickerMsg = !!quoted.stickerMessage;
        const isImageMsg   = !!quoted.imageMessage;

        if (!isStickerMsg && !isImageMsg) {
            return await sock.sendMessage(chat, {
                text: '❌ Please reply to a *sticker* or *image* only.'
            }, { quoted: msg });
        }

        await sock.sendMessage(chat, { react: { text: '✂️', key: msg.key } });

        const fakeMsg = {
            message: isStickerMsg
                ? { stickerMessage: quoted.stickerMessage }
                : { imageMessage: quoted.imageMessage },
            key: msg.key
        };

        const buffer = await downloadMediaMessage(fakeMsg, 'buffer', {});

        if (isImageMsg) {
            const webp = await sharp(buffer)
                .resize(512, 512, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
                .webp()
                .toBuffer();
            await sock.sendMessage(chat, { sticker: webp }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { sticker: buffer }, { quoted: msg });
        }
    } catch (e) {
        console.error('Take Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to take sticker.' }, { quoted: msg });
    }
};
