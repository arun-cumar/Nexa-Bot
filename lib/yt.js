// © 2026 arun•°Cumar. All Rights Reserved.
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);
const temp = './temp';

async function ensureTemp() {
    try {
        await fs.mkdir(temp, { recursive: true });
    } catch {}
}

export const downloadYt = async (url, type = 'video') => {
    await ensureTemp();

    const ext = type === 'video' ? 'mp4' : 'mp3';
    const filePath = path.join(temp, `temp_${Date.now()}.${ext}`);

    const cmd =
        type === 'video'
            ? `yt-dlp -f "bv*+ba/b" -o "${filePath}" "${url}"`
            : `yt-dlp -x --audio-format mp3 -o "${filePath}" "${url}"`;

    try {
        await execAsync(cmd);
        return filePath;
    } catch (err) {
        throw new Error('Download failed');
    }
};

export const ytSearch = async (query) => {
    try {
        const { stdout } = await execAsync(
            `yt-dlp --print "%(title)s|%(id)s" "ytsearch1:${query}"`
        );

        const [title, id] = stdout.trim().split('|');

        return {
            title,
            url: `https://www.youtube.com/watch?v=${id}`
        };
    } catch {
        return null;
    }
};

