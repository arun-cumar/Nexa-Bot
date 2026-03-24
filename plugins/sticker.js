// © 2026 arun•°Cumar. All Rights Reserved.
import { downloadContentFromMessage } from '@whiskeysockets/baileys';
import { toSticker } from '../lib/emix.js'; 

export default async (sock, msg) => {
    const from = msg.key.remoteJid;
    
    const type = Object.keys(msg.message)[0];
    const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;
    const quotedType = quoted ? Object.keys(quoted)[0] : null;

    const isImage = type === 'imageMessage' || quotedType === 'imageMessage';
    const isVideo = type === 'videoMessage' || quotedType === 'videoMessage';

    if (isImage || isVideo) {
        try {
            await sock.sendMessage(from, { text: '⏳ Creating sticker...' });

            const mediaMsg = isImage ? 
                (msg.message?.imageMessage || quoted?.imageMessage) : 
                (msg.message?.videoMessage || quoted?.videoMessage);

            const stream = await downloadContentFromMessage(mediaMsg, isImage ? 'image' : 'video');
            let buffer = Buffer.from([]);
            for await (const chunk of stream) {
                buffer = Buffer.concat([buffer, chunk]);
            }

            const sticker = await toSticker(buffer, isVideo); 

            await sock.sendMessage(from, { sticker: sticker });

        } catch (err) {
            console.error("Sticker Error:", err);
            await sock.sendMessage(from, { text: '❌ Error: Video length might be too long or limit exceeded.' });
        }
    } else {
        await sock.sendMessage(from, { text: '❌ Please reply to an image or short video with .sticker' });
    }
};


