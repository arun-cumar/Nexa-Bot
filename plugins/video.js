import { downloadYt, ytSearch } from '../lib/yt.js';
import fs from 'fs';

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;
    if (!args[0]) {
        return sock.sendMessage(from, { text: "Provide a link or search term!" });
    }

    try {
        await sock.sendMessage(from, { text: "⏳ Processing your video..." });
        
        let url = args[0];

        if (!url.includes('http')) {
            const result = await ytSearch(args.join(' '));
            if (!result) {
                return sock.sendMessage(from, { text: "❌ Video not found." });
            }
            url = result.url;
        }

        const filePath = await downloadYt(url, 'video');

        await sock.sendMessage(from, { 
            video: { url: filePath },
            caption: "✅ Downloaded via Asura-MD"
        }, { quoted: msg });

        fs.unlinkSync(filePath);

    } catch (e) {
        console.error(e);
        await sock.sendMessage(from, { 
            text: "❌ Error downloading video." 
        });
    }
};
