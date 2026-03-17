export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const lines = [
        "Are you a parking ticket? 'Cause you've got FINE written all over you! 😍",
        "Do you believe in love at first sight, or should I walk by again? 💔",
        "Are you an angle? Because you're acute one! 📐",
        "If you were a vegetable, you'd be a cute-cumber! 🥒",
        "Do you have a map? I just got lost in your eyes! 👀",
        "Are you made of copper and tellurium? Because you're CuTe! ⚗️",
        "If you were a dessert, you'd be a sweetie-pie! 🥧",
        "Do you have a pencil? Because I want to erase your past and write our future! ✏️"
    ];
    const line = lines[Math.floor(Math.random() * lines.length)];
    await sock.sendMessage(chat, { text: `😏 *PICKUP LINE*\n\n${line}` }, { quoted: msg });
};
