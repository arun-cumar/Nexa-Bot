export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const quotes = [
        { text: "The only way to do great work is to love what you do.", author: "Steve Jobs" },
        { text: "Innovation distinguishes between a leader and a follower.", author: "Steve Jobs" },
        { text: "Life is what happens when you're busy making other plans.", author: "John Lennon" },
        { text: "The future belongs to those who believe in the beauty of their dreams.", author: "Eleanor Roosevelt" },
        { text: "It is during our darkest moments that we must focus to see the light.", author: "Aristotle" },
        { text: "The only impossible journey is the one you never begin.", author: "Tony Robbins" },
        { text: "Success is not final, failure is not fatal.", author: "Winston Churchill" },
        { text: "Believe you can and you're halfway there.", author: "Theodore Roosevelt" },
        { text: "Don't watch the clock; do what it does. Keep going.", author: "Sam Levenson" },
        { text: "The way to get started is to quit talking and begin doing.", author: "Walt Disney" }
    ];
    const quote = quotes[Math.floor(Math.random() * quotes.length)];
    await sock.sendMessage(chat, {
        text: `💭 *QUOTE*\n\n"${quote.text}"\n\n— ${quote.author}`
    }, { quoted: msg });
};
