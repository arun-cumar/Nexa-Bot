export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (args.length < 2) return await sock.sendMessage(chat, { text: "❌ Usage: `.translate en|hi|es <text>`" }, { quoted: msg });
    const lang = args[0].toLowerCase();
    const text = args.slice(1).join(' ');
    const translations = {
        hi: { hello: "नमस्ते", bye: "अलविदा", thanks: "धन्यवाद", love: "प्यार" },
        es: { hello: "Hola", bye: "Adiós", thanks: "Gracias", love: "Amor" },
        fr: { hello: "Bonjour", bye: "Au revoir", thanks: "Merci", love: "Amour" }
    };
    const trans = translations[lang]?.[text.toLowerCase()] || "Translation not available";
    await sock.sendMessage(chat, { text: `🌐 *${text}* → *${trans}*` }, { quoted: msg });
};
