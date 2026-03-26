import fs from "fs";

export async function handleMentionSticker(sock, msg, from) {
    try {
        const mentions = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid || [];
        
        if (mentions.length > 5) {
            const stickerPath = './media/sticker.webp';
            
            if (fs.existsSync(stickerPath)) {
                await sock.sendMessage(from, {
                    sticker: fs.readFileSync(stickerPath)
                }, { quoted: msg });
                return true; 
            }
        }
        return false;
    } catch (err) {
        console.error("❌ Mention Sticker Error:", err);
        return false;
    }
}
