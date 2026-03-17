export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const news = `📰 *LATEST NEWS*\n\n1. Tech Giant Releases AI Model\n2. New Space Discovery Found\n3. Market Reaches New High\n4. Climate Action Summit Begins\n5. Sports Team Wins Championship`;
    await sock.sendMessage(chat, { text: news }, { quoted: msg });
};
