import ytSearch from 'yt-search';
import axios from 'axios';
import fs from 'fs';
import path from 'path';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;

    const sub  = args[0]?.toLowerCase();
    const query = args.slice(1).join(' ');

    if (!sub || !['yt', 'song', 'video'].includes(sub)) {
        return await sock.sendMessage(chat, {
            text:
`╭━━〔 📥 *DOWNLOADER* 〕━━╮
┃
┃  *.downloader yt* <query>
┃    Search YouTube videos
┃
┃  *.downloader song* <title>
┃    Search & download audio
┃
┃  *.downloader video* <title>
┃    Search YouTube video info
┃
╰━━━━━━━━━━━━━━━━━━━━━╯`
        }, { quoted: msg });
    }

    if (!query) {
        return await sock.sendMessage(chat, {
            text: `❌ Please provide a search query.\n\nExample: *.downloader ${sub} Shape of You*`
        }, { quoted: msg });
    }

    await sock.sendMessage(chat, { react: { text: '🔍', key: msg.key } });

    try {
        const results = await ytSearch(query);
        const video   = results.videos[0];

        if (!video) {
            return await sock.sendMessage(chat, { text: '❌ No results found for: *' + query + '*' }, { quoted: msg });
        }

        const info =
`╭━━〔 🎬 *YOUTUBE* 〕━━╮
┃
┃  📌 *Title:* ${video.title}
┃  ⏱️ *Duration:* ${video.timestamp}
┃  👁️ *Views:* ${Number(video.views).toLocaleString()}
┃  📅 *Uploaded:* ${video.ago}
┃  👤 *Author:* ${video.author?.name || 'Unknown'}
┃  🔗 *URL:* ${video.url}
┃
╰━━━━━━━━━━━━━━━━━━━━━╯`;

        if (sub === 'yt') {
            if (video.thumbnail) {
                await sock.sendMessage(chat, {
                    image: { url: video.thumbnail },
                    caption: info
                }, { quoted: msg });
            } else {
                await sock.sendMessage(chat, { text: info }, { quoted: msg });
            }
            return;
        }

        if (sub === 'song' || sub === 'video') {
            await sock.sendMessage(chat, {
                text: info + '\n\n⚠️ *Direct download requires a premium API key.*\n\nShare the link above to download manually.'
            }, { quoted: msg });
        }
    } catch (e) {
        console.error('Downloader Error:', e);
        await sock.sendMessage(chat, { text: '❌ Search failed. Please try again.' }, { quoted: msg });
    }
};
