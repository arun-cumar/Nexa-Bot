import fs from 'fs';

export default async (sock, msg, args) => {
    const chat = msg.key.remoteJid;
    const imagePath = './media/nexa.jpg';

    try {
        await sock.sendMessage(chat, { react: { text: "📡", key: msg.key } });

        const { key } = await sock.sendMessage(chat, { text: "🚀 Connecting to NEXA-BOT Server..." });

        const frames = [
            "📶 Tᴇsᴛɪɴɢ Lᴀᴛᴇɴᴄʏ...",
            "📡 Nᴇᴛᴡᴏʀᴋ: Sᴛᴀʙʟᴇ"          
        ];

        for (let frame of frames) {
            await new Promise(resolve => setTimeout(resolve, 500)); 
            await sock.sendMessage(chat, { text: frame, edit: key });
        }

        const ping = Date.now() - (msg.messageTimestamp * 1000);
        const speedStatus = ping < 500 ? "Turbo 🚀" : "Normal ⚡";
        const netStatus = "🟢 High Speed";

        const pingMsg = `
 🚀𝚂𝚙𝚎𝚎𝚍 : ${speedStatus}
 📡𝙻𝚊𝚝𝚎𝚗𝚌𝚢 : ${Math.abs(ping)} 𝚖𝚜
 📶𝙽𝚎𝚝𝚠𝚘𝚛𝚔 : ${netStatus}`;

        if (fs.existsSync(imagePath)) {
            await sock.sendMessage(chat, { 
                image: fs.readFileSync(imagePath), 
                caption: pingMsg 
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, { text: pingMsg }, { quoted: msg });
        }
       
    } catch (e) {
        console.error("Ping Error:", e);
    }
};
