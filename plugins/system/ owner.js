import fs from 'fs';

export default async (sock, msg, args) => {
const chat = msg.key.remoteJid;
const thumbPath = './media/nexa.jpg';

const ownerMsg = ` 

╔══════════════╗
Nexa Bot MD Developer
arun•°Cumar
╚══════════════╝

Join:
https://whatsapp.com/channel/0029VbB59W9GehENxhoI5l24
`;

   const vcard = 'BEGIN:VCARD\n' + 'VERSION:3.0\n' + 'FN:arun•°Cumar\n' + 'ORG:Nexa-Bot MD Developer;\n' + 'TEL;type=CELL;type=VOICE:+91 7736811908\n' + 'END:VCARD'; try { if (fs.existsSync(thumbPath)) { await sock.sendMessage(chat, { image: fs.readFileSync(thumbPath), caption: ownerMsg }, { quoted: msg }); } else { await sock.sendMessage(chat, { text: ownerMsg }, { quoted: msg }); } await sock.sendMessage(chat, { contacts: { displayName: 'arun•°Cumar', contacts: [{ vcard }] } }, { quoted: msg }); await sock.sendMessage(chat, { location: { degreesLatitude: 8.9404, degreesLongitude: 76.6573, name: 'arun•°Cumar - Nexa-Bot-MD', address: 'Kerala, India' } }, { quoted: msg }); } catch (e) { console.error("Owner Cmd Error:", e); } 
};



