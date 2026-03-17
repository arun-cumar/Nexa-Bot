export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const jokes = [
        "Why don't scientists trust atoms?\nBecause they make up everything! 😂",
        "Why did the scarecrow win an award?\nHe was outstanding in his field! 🌾",
        "I told my computer I needed a break and now it won't stop sending me Kit-Kat ads. 💻",
        "Why do Java developers wear glasses?\nBecause they don't C#! 😄",
        "How many programmers does it take to change a light bulb?\nNone, that's a hardware problem! 💡",
        "Why did the developer go broke?\nHe used up all his cache! 💰",
        "What do you call a programmer from Finland?\nNoka! 📱",
        "Why do programmers prefer dark mode?\nBecause light attracts bugs! 🐛",
        "How many clicks to the center of a Tootsie Pop?\nThe world may never know... 🍭",
        "What's orange and sounds like a parrot?\nA carrot! 🥕"
    ];
    const joke = jokes[Math.floor(Math.random() * jokes.length)];
    await sock.sendMessage(chat, { text: `😂 *JOKE*\n\n${joke}` }, { quoted: msg });
};
