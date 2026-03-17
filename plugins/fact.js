export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const facts = [
        "Honey never spoils. Archaeologists have found 3000-year-old honey that was still edible! 🍯",
        "A day on Venus is longer than its year! 🪐",
        "Bananas are berries, but strawberries aren't! 🍌",
        "Your body contains about 37 trillion cells. 🧬",
        "The shortest war ever lasted 38 minutes! ⚔️",
        "Octopuses have three hearts and blue blood! 🐙",
        "A group of flamingos is called a 'flamboyance'! 🦩",
        "The Great Wall of China is not visible from space! 🧱",
        "Cows have best friends and get stressed when separated! 🐄",
        "Humans share 99% DNA with chimpanzees! 🦧"
    ];
    const fact = facts[Math.floor(Math.random() * facts.length)];
    await sock.sendMessage(chat, { text: `💡 *FACT*\n\n${fact}` }, { quoted: msg });
};
