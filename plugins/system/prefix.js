import { setPrefix, getPrefix } from '../../lib/settings/prefix.js';

export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;
    const currentPrefix = getPrefix();

    // prefix (to check)
    if (args.length === 0) {
        return await sock.sendMessage(from, { 
            text: `Current Prefix is: *${currentPrefix}*` 
        }, { quoted: msg });
    }

    // setprefix 
    const newPrefix = args[0];
    
    // Safety checker
    if (newPrefix.length > 3) {
        return await sock.sendMessage(from, { text: ".Prefix ! " });
    }

    setPrefix(newPrefix);
    await sock.sendMessage(from, { 
        text: `✅ Prefix updated to: *${newPrefix}*` 
    }, { quoted: msg });
};
