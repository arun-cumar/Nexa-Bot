export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (args.length < 2) return await sock.sendMessage(chat, { text: '❌ Usage: `.poll "question" "option1" "option2"`' }, { quoted: msg });
    const question = args[0];
    const options = args.slice(1);
    let poll = `📋 *POLL*\n\n${question}\n\n`;
    options.forEach((opt, i) => { poll += `${i + 1}. ${opt}\n`; });
    await sock.sendMessage(chat, { text: poll }, { quoted: msg });
};
