// © 2026 arun•°Cumar. All Rights Reserved.
import { imageToSticker, videoToSticker, gifToSticker } from '../../lib/emix.js';

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;

    try {
        
        const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;
        if (!quoted) {
            return sock.sendMessage(from, { text: "Reply to an image, video, or gif to make a sticker!" });
        }

        let buffer;

        if (quoted.imageMessage) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await imageToSticker(buffer, 'jpg');
            return await sock.sendMessage(from, { sticker });
        }

        else if (quoted.videoMessage?.gifPlayback) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await gifToSticker(buffer, 'mp4');
            return await sock.sendMessage(from, { sticker });
        }

        else if (quoted.videoMessage) {
            buffer = await sock.downloadMediaMessage({ message: quoted });
            const sticker = await videoToSticker(buffer, 'mp4');
            return await sock.sendMessage(from, { sticker });
        }

        else {
            await sock.sendMessage(from, { text: "Please reply to a valid media (Image/Video/GIF)" });
        }

    } catch (err) {
        console.error("Media Convert Error:", err);
        await sock.sendMessage(from, { text: "❌ Convert failed" });
    }
};
