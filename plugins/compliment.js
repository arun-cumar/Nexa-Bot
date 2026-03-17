export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const compliments = [
        "You light up the room! ✨",
        "You're an awesome friend! 👫",
        "You're a gift to those around you! 🎁",
        "You're an incredible human! 💫",
        "You're like sunshine on a rainy day! ☀️",
        "You bring out the best in other people! 💖",
        "You're one of a kind! 🌟",
        "Your potential seems limitless! 🚀",
        "You're a smart cookie! 🍪",
        "Great sense of humor! 😄"
    ];
    const compliment = compliments[Math.floor(Math.random() * compliments.length)];
    await sock.sendMessage(chat, { text: `😊 *COMPLIMENT*\n\n${compliment}` }, { quoted: msg });
};
