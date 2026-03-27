// © 2026 arun•°Cumar. All Rights Reserved.

import { checkAdmin } from '../settings/check.js';

export default async function tagAll(sock, msg, args) {
    const chatId = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;

    try {
        const isAdminUser = await checkAdmin(sock, chatId, sender);

        if (!isAdminUser) {
            await sock.sendMessage(chatId, {
                text: '❌ Only group admins can use this command.'
            }, { quoted: msg });
            return;
        }

        const groupMetadata = await sock.groupMetadata(chatId);
        const participants = groupMetadata.participants;

        if (!participants || participants.length === 0) {
            await sock.sendMessage(chatId, {
                text: 'No participants found in the group.'
            });
            return;
        }

        let text = '🔊 *Hello Everyone:*\n\n';

        for (let p of participants) {
            text += `@${p.id.split('@')[0]}\n`;
        }

        await sock.sendMessage(chatId, {
            text: text,
            mentions: participants.map(p => p.id)
        }, { quoted: msg });

    } catch (error) {
        console.log("TagAll Error:", error);
        await sock.sendMessage(chatId, {
            text: 'Failed to tag all members.'
        });
    }
}
