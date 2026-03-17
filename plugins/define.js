export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide a word: `.define word`" }, { quoted: msg });
    const word = args[0].toLowerCase();
    const defs = { bot: "An automated program or software agent", code: "Computer instructions written in a language", api: "Interface for software applications to communicate", web: "System of interconnected documents on internet", ai: "Artificial Intelligence - machine learning", data: "Facts and information collected for analysis", crypto: "Digital currency using cryptography", cloud: "Remote computing services over internet", cache: "Fast storage for frequently accessed data", bug: "Error or flaw in software program" };
    const def = defs[word] || "Definition not found. Try another word!";
    await sock.sendMessage(chat, { text: `📖 *DEFINE: ${word.toUpperCase()}*\n\n${def}` }, { quoted: msg });
};
