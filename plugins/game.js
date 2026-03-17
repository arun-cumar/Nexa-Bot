export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const sub = args[0]?.toLowerCase();

    const truths = [
        "What is your biggest fear?", "What is the most embarrassing thing you've done?",
        "Have you ever lied to your best friend?", "What is your biggest secret?",
        "Who was your first crush?", "What is your biggest regret?",
        "Have you ever cheated on a test?", "What is something you've never told anyone?",
        "What is your guilty pleasure?", "What is the weirdest dream you've had?"
    ];

    const dares = [
        "Send a funny selfie!", "Text your crush right now.",
        "Sing a song for 30 seconds.", "Do 10 push-ups.",
        "Speak in an accent for the next 2 minutes.",
        "Set a silly photo as your profile picture for 1 hour.",
        "Tell a joke that makes everyone laugh.",
        "Imitate a celebrity for 1 minute.",
        "Share your most embarrassing photo.",
        "Call someone and sing Happy Birthday."
    ];

    const eightBallAnswers = [
        "✅ It is certain.", "✅ Without a doubt.", "✅ Yes, definitely!",
        "✅ You may rely on it.", "🤔 Ask again later.", "🤔 Cannot predict now.",
        "🤔 Concentrate and ask again.", "❌ Don't count on it.",
        "❌ My reply is no.", "❌ Very doubtful."
    ];

    if (!sub) {
        return await sock.sendMessage(chat, {
            text:
`╭━━〔 🎮 *GAMES* 〕━━╮
┃
┃  *.game truth*  – Truth question
┃  *.game dare*   – Dare challenge
┃  *.game 8ball* <question>
┃  *.game dice*   – Roll a dice
┃  *.game rps* <rock/paper/scissors>
┃  *.game coin*   – Flip a coin
┃
╰━━━━━━━━━━━━━━━━━╯`
        }, { quoted: msg });
    }

    if (sub === 'truth') {
        const q = truths[Math.floor(Math.random() * truths.length)];
        return await sock.sendMessage(chat, {
            text: `🎯 *TRUTH*\n\n❓ ${q}`
        }, { quoted: msg });
    }

    if (sub === 'dare') {
        const d = dares[Math.floor(Math.random() * dares.length)];
        return await sock.sendMessage(chat, {
            text: `🔥 *DARE*\n\n💪 ${d}`
        }, { quoted: msg });
    }

    if (sub === '8ball') {
        const question = args.slice(1).join(' ');
        if (!question) return await sock.sendMessage(chat, { text: '❌ Ask a question: `.game 8ball <question>`' }, { quoted: msg });
        const answer = eightBallAnswers[Math.floor(Math.random() * eightBallAnswers.length)];
        return await sock.sendMessage(chat, {
            text: `🎱 *MAGIC 8-BALL*\n\n❓ ${question}\n\n${answer}`
        }, { quoted: msg });
    }

    if (sub === 'dice') {
        const roll = Math.floor(Math.random() * 6) + 1;
        const faces = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
        return await sock.sendMessage(chat, {
            text: `🎲 *DICE ROLL*\n\nYou rolled: ${faces[roll]} *${roll}*`
        }, { quoted: msg });
    }

    if (sub === 'coin') {
        const result = Math.random() < 0.5 ? '🪙 *HEADS*' : '🪙 *TAILS*';
        return await sock.sendMessage(chat, {
            text: `🪙 *COIN FLIP*\n\n${result}!`
        }, { quoted: msg });
    }

    if (sub === 'rps') {
        const choices = ['rock', 'paper', 'scissors'];
        const icons   = { rock: '🪨', paper: '📄', scissors: '✂️' };
        const player  = args[1]?.toLowerCase();

        if (!choices.includes(player)) {
            return await sock.sendMessage(chat, {
                text: '❌ Choose: `.game rps rock` / `paper` / `scissors`'
            }, { quoted: msg });
        }

        const bot = choices[Math.floor(Math.random() * 3)];
        let result;
        if (player === bot) result = "🤝 It's a *draw*!";
        else if (
            (player === 'rock'     && bot === 'scissors') ||
            (player === 'paper'    && bot === 'rock')     ||
            (player === 'scissors' && bot === 'paper')
        ) result = '🎉 You *win*!';
        else result = '😈 Bot *wins*!';

        return await sock.sendMessage(chat, {
            text: `✊ *ROCK PAPER SCISSORS*\n\nYou: ${icons[player]} *${player}*\nBot: ${icons[bot]} *${bot}*\n\n${result}`
        }, { quoted: msg });
    }

    await sock.sendMessage(chat, { text: '❌ Unknown game. Use `.game` to see all games.' }, { quoted: msg });
};
