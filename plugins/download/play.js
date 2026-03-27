// © 2026 arun•°Cumar. All Rights Reserved.
import { downloadYt, ytSearch } from '../../lib/yt.js';
import { toAudio, toPTT } from '../../lib/emix.js';
import fs from 'fs';

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;
    if (!args[0]) {
        return sock.sendMessage(from, { text: "What song do you want to play?" });
    }

    try {
        await sock.sendMessage(from, { text: "🎶 Fetching audio..." });

        let url = args[0];

        if (!url.includes('http')) {
            const result = await ytSearch(args.join(' '));
            if (!result) {
                return sock.sendMessage(from, { text: "❌ Song not found." });
            }
            url = result.url;
        }

        const filePath = await downloadYt(url, 'audio');

        // Check if user wants voice note
        if (args.includes('ptt')) {
            const opusBuffer = await toPTT(filePath);

            await sock.sendMessage(from, {
                audio: opusBuffer,
                mimetype: 'audio/ogg; codecs=opus',
                ptt: true
            }, { quoted: msg });

        } else {
            const audioBuffer = await toAudio(filePath);

            await sock.sendMessage(from, {
                audio: audioBuffer,
                mimetype: 'audio/mpeg'
            }, { quoted: msg });
        }

        fs.unlinkSync(filePath);

    } catch (e) {
        console.error(e);
        await sock.sendMessage(from, { text: "❌ Audio Play Error." });
    }
};
