export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;

    if (!args.length) {
        return await sock.sendMessage(chat, {
            text: '❌ Please provide text.\n\nUsage: *.fancy* <text>\nExample: *.fancy* Hello World'
        }, { quoted: msg });
    }

    const text = args.join(' ');

    const fonts = {
        bold: Array.from('abcdefghijklmnopqrstuvwxyz').reduce((m, c, i) => {
            m[c] = '𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳'[i];
            m[c.toUpperCase()] = '𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙'[i];
            return m;
        }, {}),
        italic: Array.from('abcdefghijklmnopqrstuvwxyz').reduce((m, c, i) => {
            m[c] = '𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻'[i];
            m[c.toUpperCase()] = '𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡'[i];
            return m;
        }, {}),
        script: Array.from('abcdefghijklmnopqrstuvwxyz').reduce((m, c, i) => {
            m[c] = '𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏'[i];
            m[c.toUpperCase()] = '𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵'[i];
            return m;
        }, {}),
        bubble: Array.from('abcdefghijklmnopqrstuvwxyz').reduce((m, c, i) => {
            m[c] = 'ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ'[i];
            m[c.toUpperCase()] = 'ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ'[i];
            return m;
        }, {}),
        mono: Array.from('abcdefghijklmnopqrstuvwxyz').reduce((m, c, i) => {
            m[c] = '𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣'[i];
            m[c.toUpperCase()] = '𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉'[i];
            return m;
        }, {})
    };

    const convert = (map) => [...text].map(c => map[c] || c).join('');

    const result =
`╭━━〔 ✨ *FANCY TEXT* 〕━━╮

🔤 *Original:* ${text}

𝐁𝐎𝐋𝐃: ${convert(fonts.bold)}
𝘐𝘵𝘢𝘭𝘪𝘤: ${convert(fonts.italic)}
𝒮𝒸𝓇𝒾𝓅𝓉: ${convert(fonts.script)}
Ⓑⓤⓑⓑⓛⓔ: ${convert(fonts.bubble)}
𝙼𝚘𝚗𝚘: ${convert(fonts.mono)}

╰━━━━━━━━━━━━━━━━━╯`;

    await sock.sendMessage(chat, { text: result }, { quoted: msg });
};
