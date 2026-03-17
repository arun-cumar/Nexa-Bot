import config from '../config.js';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;

    if (!chat.endsWith('@g.us')) {
        return await sock.sendMessage(chat, { text: '❌ This command works in *groups only*.' }, { quoted: msg });
    }

    const sub = args[0]?.toLowerCase();

    if (!sub) {
        return await sock.sendMessage(chat, {
            text:
`╭━━〔 ⚙️ *GROUP MANAGE* 〕━━╮
┃
┃  *.manage kick* @user
┃  *.manage promote* @user
┃  *.manage demote* @user
┃  *.manage mute*   – Mute group
┃  *.manage unmute* – Unmute group
┃
╰━━━━━━━━━━━━━━━━━━━━━╯`
        }, { quoted: msg });
    }

    try {
        const meta = await sock.groupMetadata(chat);
        const botId = sock.user.id.split(':')[0] + '@s.whatsapp.net';
        const admins = meta.participants.filter(p => p.admin).map(p => p.id);
        const isAdmin  = admins.includes(sender);
        const isOwner  = config.OWNER_NUMBER.includes(sender.split('@')[0]);
        const isBotAdmin = admins.includes(botId);

        if (!isAdmin && !isOwner) {
            return await sock.sendMessage(chat, { text: '❌ Only *admins* can manage the group.' }, { quoted: msg });
        }
        if (!isBotAdmin) {
            return await sock.sendMessage(chat, { text: '❌ Make me an *admin* first!' }, { quoted: msg });
        }

        const mentioned = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid || [];
        const target = mentioned[0];

        if (['kick', 'promote', 'demote'].includes(sub)) {
            if (!target) {
                return await sock.sendMessage(chat, { text: `❌ Mention a user: *.manage ${sub} @user*` }, { quoted: msg });
            }

            if (sub === 'kick') {
                await sock.groupParticipantsUpdate(chat, [target], 'remove');
                await sock.sendMessage(chat, {
                    text: `✅ @${target.split('@')[0]} has been *kicked*!`,
                    mentions: [target]
                }, { quoted: msg });
            } else if (sub === 'promote') {
                await sock.groupParticipantsUpdate(chat, [target], 'promote');
                await sock.sendMessage(chat, {
                    text: `✅ @${target.split('@')[0]} has been *promoted to admin*!`,
                    mentions: [target]
                }, { quoted: msg });
            } else if (sub === 'demote') {
                await sock.groupParticipantsUpdate(chat, [target], 'demote');
                await sock.sendMessage(chat, {
                    text: `✅ @${target.split('@')[0]} has been *demoted*!`,
                    mentions: [target]
                }, { quoted: msg });
            }
        } else if (sub === 'mute') {
            await sock.groupSettingUpdate(chat, 'announcement');
            await sock.sendMessage(chat, { text: '🔇 Group has been *muted* (only admins can send).' }, { quoted: msg });
        } else if (sub === 'unmute') {
            await sock.groupSettingUpdate(chat, 'not_announcement');
            await sock.sendMessage(chat, { text: '🔊 Group has been *unmuted* (everyone can send).' }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: '❌ Unknown sub-command. Use `.manage` for help.' }, { quoted: msg });
        }
    } catch (e) {
        console.error('Manage Error:', e);
        await sock.sendMessage(chat, { text: '❌ Failed to execute command: ' + e.message }, { quoted: msg });
    }
};
