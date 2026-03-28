import { downloadContentFromMessage } from '@whiskeysockets/baileys';

/**
 * Universal Media Downloader 
 */

export const downloadMedia = async (message) => {
    // 1. Message type kandupidikkunnu
    let type = Object.keys(message)[0];
    let msgContent = message[type];

    // 2. View Once handling (V2 and regular)
    if (type === 'viewOnceMessageV2' || type === 'viewOnceMessage') {
        msgContent = msgContent.message;
        type = Object.keys(msgContent)[0];
        msgContent = msgContent[type];
    }

    // 3. Mapping Baileys types to downloader types
    const mimeMap = {
        imageMessage: 'image',
        videoMessage: 'video', 
        audioMessage: 'audio',
        stickerMessage: 'sticker',
        documentMessage: 'document'
    };

    let downloadType = mimeMap[type];

    if (!downloadType || !msgContent) {
        throw new Error("Ithu support cheyyatha media type aanu!");
    }

    try {
        // 4. Downloading stream
        const stream = await downloadContentFromMessage(msgContent, downloadType);
        let buffer = Buffer.from([]);
        
        for await (const chunk of stream) {
            buffer = Buffer.concat([buffer, chunk]);
        }
        
        return buffer;
    } catch (err) {
        throw new Error("Download Failed: " + err.message);
    }
};
