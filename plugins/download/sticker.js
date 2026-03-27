// © 2026 arun•°Cumar. All Rights Reserved.
import { imageToSticker, videoToSticker, gifToSticker, toGif } from '../../lib/emix.js';

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;

    try {
        const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;
        if (!quoted) {
            return sock.sendMessage(from, { text: "Reply to image/video/sticker" });
        }

        let buffer;
        let ext;

        if (quoted.imageMessage) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await imageToSticker(buffer, 'jpg');
            await sock.sendMessage(from, { sticker });
        }

        else if (quoted.videoMessage) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await videoToSticker(buffer, 'mp4');
            await sock.sendMessage(from, { sticker });
        }

        else if (quoted.stickerMessage) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const gif = await toGif(buffer, 'webp');

            await sock.sendMessage(from, {
                video: gif,
                gifPlayback: true
            });
        }

        else if (quoted.videoMessage?.gifPlayback) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await gifToSticker(buffer, 'mp4');
            await sock.sendMessage(from, { sticker });
        }

    } catch (err) {
        console.log("Media Convert Error:", err);
        await sock.sendMessage(from, { text: "❌ Convert failed" });
    }
};
