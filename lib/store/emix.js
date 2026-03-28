// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const tmpDir = path.join(__dirname, '../tmp');

if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir);

// Main ffmpeg function
function ffmpeg(buffer, args = [], inputExt = '', outputExt = '') {
    return new Promise(async (resolve, reject) => {
        try {
            const inputPath = path.join(tmpDir, `${Date.now()}.${inputExt}`);
            const outputPath = `${inputPath}.${outputExt}`;

            await fs.promises.writeFile(inputPath, buffer);

            const ff = spawn('ffmpeg', [
                '-y',
                '-i', inputPath,
                ...args,
                outputPath
            ]);

            ff.on('error', reject);

            ff.on('close', async (code) => {
                try {
                    await fs.promises.unlink(inputPath);

                    if (code !== 0) {
                        return reject(new Error(`FFmpeg exit code ${code}`));
                    }

                    const data = await fs.promises.readFile(outputPath);
                    await fs.promises.unlink(outputPath);

                    resolve(data);
                } catch (e) {
                    reject(e);
                }
            });

        } catch (err) {
            reject(err);
        }
    });
}


export const imageToSticker = (buffer, ext) =>
    ffmpeg(buffer, [
        '-vcodec', 'libwebp',
        '-vf',
        "scale=512:512:force_original_aspect_ratio=decrease,fps=15,pad=512:512:-1:-1:color=white@0.0",
        '-lossless', '1',
        '-compression_level', '6',
        '-q:v', '50',
        '-loop', '0',
        '-preset', 'default',
        '-an',
        '-vsync', '0'
    ], ext, 'webp');

export const videoToSticker = (buffer, ext) =>
    ffmpeg(buffer, [
        '-vcodec', 'libwebp',
        '-vf',
        "scale=512:512:force_original_aspect_ratio=decrease,fps=15,pad=512:512:-1:-1:color=white@0.0",
        '-loop', '0',
        '-ss', '00:00:00',
        '-t', '00:00:10',
        '-preset', 'default',
        '-an',
        '-vsync', '0'
    ], ext, 'webp');

export const gifToSticker = (buffer, ext) =>
    ffmpeg(buffer, [
        '-vcodec', 'libwebp',
        '-vf',
        "fps=15,scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:-1:-1:color=white@0.0",
        '-loop', '0',
        '-preset', 'default',
        '-an',
        '-vsync', '0'
    ], ext, 'webp');

export const toVideo = (buffer, ext) =>
    ffmpeg(buffer, [
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-crf', '28',
        '-preset', 'fast'
    ], ext, 'mp4');

export const toAudio = (buffer, ext) =>
    ffmpeg(buffer, [
        '-vn',
        '-ac', '2',
        '-b:a', '128k',
        '-ar', '44100'
    ], ext, 'mp3');

export const toPTT = (buffer, ext) =>
    ffmpeg(buffer, [
        '-vn',
        '-c:a', 'libopus',
        '-b:a', '128k',
        '-vbr', 'on'
    ], ext, 'opus');

/**
 * Vv
 */
export const toViewOnce = (content) => {
    return {
        ...content,
        viewOnce: true
    };
};

// 1. Photo View Once
export const toViewOncePhoto = (buffer, caption = '') => {
    return { image: buffer, caption, viewOnce: true };
};

// 2. Video View Once
export const toViewOnceVideo = (buffer, caption = '') => {
    return { video: buffer, caption, viewOnce: true };
};

// 3. Voice (PTT) View Once 
export const toViewOnceVoice = (buffer) => {
    return { audio: buffer, ptt: true, viewOnce: true };
};
