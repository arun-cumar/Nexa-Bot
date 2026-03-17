export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    if (!args.length) return await sock.sendMessage(chat, { text: '❌ Usage: `.math add 5 10` or `.math sqrt 16`' }, { quoted: msg });
    const op = args[0].toLowerCase();
    const nums = args.slice(1).map(Number);
    let result;
    if (op === 'add') result = nums.reduce((a, b) => a + b, 0);
    else if (op === 'sub') result = nums.reduce((a, b) => a - b);
    else if (op === 'mul') result = nums.reduce((a, b) => a * b, 1);
    else if (op === 'div') result = nums.reduce((a, b) => a / b);
    else if (op === 'sqrt') result = Math.sqrt(nums[0]);
    else if (op === 'pow') result = Math.pow(nums[0], nums[1]);
    else return await sock.sendMessage(chat, { text: '❌ Unknown operation' }, { quoted: msg });
    await sock.sendMessage(chat, { text: `🧮 *${op.toUpperCase()}*\n\nResult: ${result}` }, { quoted: msg });
};
