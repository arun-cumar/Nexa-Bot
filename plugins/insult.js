export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const insults = [
        "You're like a software update – nobody asked for you, and you just make things worse! 💾",
        "Your brain is like an antivirus – it protects you against nothing! 🦠",
        "You have the personality of a sleeping browser tab! 😴",
        "If your IQ was gasoline, you couldn't drive an ant to the grocery store! 🐜",
        "You're not stupid, you just have bad luck when you think! 🍀",
        "I'd tell you to go to hell, but I don't want you living in my neighborhood! 😈",
        "You're the reason we have instruction labels on everything! 📋",
        "Your face would turn a reflection into an abstract painting! 🎨"
    ];
    const insult = insults[Math.floor(Math.random() * insults.length)];
    await sock.sendMessage(chat, { text: `💢 *INSULT*\n\n${insult}` }, { quoted: msg });
};
