import axios from 'axios';
import fs from 'fs';
import path from 'path';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const url = args.join(' ');
    
    if (!url) {
        return await sock.sendMessage(chat, {
            text: `❌ Provide YouTube URL\n\nUsage: *.video* <youtube_url>\n\nExamples:\n.video https://youtu.be/ti5MaCUuCe4\n.video https://www.youtube.com/watch?v=ABC123`
        }, { quoted: msg });
    }
    
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        return await sock.sendMessage(chat, {
            text: '❌ Invalid YouTube URL. Must be from youtube.com or youtu.be'
        }, { quoted: msg });
    }
    
    await sock.sendMessage(chat, { react: { text: '⏳', key: msg.key } });
    
    const tempDir = `/tmp/yt_${Date.now()}`;
    const videoPath = path.join(tempDir, 'video.mp4');
    
    try {
        fs.mkdirSync(tempDir, { recursive: true });
        
        // Get video info
        const apiUrl = `https://api.sparky.biz.id/api/downloader/ytv?url=${encodeURIComponent(url)}`;
        const response = await axios.get(apiUrl, { timeout: 15000 });
        
        if (!response.data.status || !response.data.data) {
            return await sock.sendMessage(chat, {
                text: '❌ Failed to fetch video. The video may be:\n• Private\n• Deleted\n• Not available in your region'
            }, { quoted: msg });
        }
        
        const data = response.data.data;
        const title = data.title || 'YouTube Video';
        const downloadUrl = data.url;
        
        await sock.sendMessage(chat, { react: { text: '📥', key: msg.key } });
        
        // Download the video file
        console.log('📥 Downloading video from:', downloadUrl);
        const videoRes = await axios.get(downloadUrl, {
            responseType: 'arraybuffer',
            timeout: 120000,
            maxContentLength: 524288000, // 500MB limit
            maxBodyLength: 524288000
        });
        
        fs.writeFileSync(videoPath, videoRes.data);
        
        const fileSize = fs.statSync(videoPath).size;
        console.log(`✅ Video downloaded: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);
        
        // Send video directly
        await sock.sendMessage(chat, {
            video: fs.readFileSync(videoPath),
            caption: `▶️ *${title}*\n\n> Downloaded by Nexa-Bot MD`
        }, { quoted: msg });
        
        // Cleanup
        fs.rmSync(tempDir, { recursive: true });
        
    } catch (e) {
        console.error('YouTube Downloader Error:', e.message);
        if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
        }
        
        await sock.sendMessage(chat, {
            text: '❌ Download failed.\n\nPossible reasons:\n• Video too large\n• Download link expired\n• Network timeout\n\nTry again later!'
        }, { quoted: msg });
    }
};
