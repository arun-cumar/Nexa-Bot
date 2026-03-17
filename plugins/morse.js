export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: "❌ Provide text: `.morse hello`" }, { quoted: msg });
    const morse = { a: '.-', b: '-...', c: '-.-.', d: '-..', e: '.', f: '..-.', g: '--.', h: '....', i: '..', j: '.---', k: '-.-', l: '.-..', m: '--', n: '-.', o: '---', p: '.--.', q: '--.-', r: '.-.', s: '...', t: '-', u: '..-', v: '...-', w: '.--', x: '-..-', y: '-.--', z: '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.' };
    const text = args.join('').toLowerCase();
    const result = [...text].map(c => morse[c] || c).join(' ');
    await sock.sendMessage(chat, { text: `📡 *MORSE CODE*\n\n${result}` }, { quoted: msg });
};
