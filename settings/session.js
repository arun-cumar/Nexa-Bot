// © 2026 arun•°Cumar. All Rights Reserved.
import chalk from 'chalk';
import readline from 'readline';

export async function handleSession(sock) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const question = (text) => new Promise((resolve) => rl.question(text, resolve));

    console.clear();

    const line = chalk.cyan('═'.repeat(46));

    console.log(chalk.cyan(`
╔${'═'.repeat(46)}╗
║ 🚀 NEXA BOT SYSTEM  ║
║ Developed by arun•°Cumar ║
╚${'═'.repeat(46)}╝
`));

    if (!sock.authState.creds.registered) {
        console.log(chalk.whiteBright('\n   [ PAIRING LOGIN ]\n'));

        const phoneNumber = await question(
            chalk.yellow('   📞 Enter Number (91XXXXXXXXXX): ')
        );

        const cleanNumber = phoneNumber.replace(/[^0-9]/g, '');

        if (cleanNumber.length < 10) {
            console.log(chalk.red('   ❌ Invalid Phone Number!'));
            rl.close();
            return;
        }

        console.log(chalk.blue('\n   ⏳ Requesting Pairing Code...\n'));

        try {
            const code = await sock.requestPairingCode(cleanNumber);

            console.log(chalk.greenBright(`
╔${'═'.repeat(46)}╗
║ 🗝 YOUR PAIRING Code ║
╠${'═'.repeat(46)}╣
║   ${code}       ║
╚${'═'.repeat(46)}╝
`));

            console.log(
                chalk.gray('   💡 WhatsApp > Linked Devices > Link with Phone Number\n')
            );

        } catch (err) {
            console.log(chalk.red('   ❌ Error: ' + err.message));
        }
    }

    rl.close();
}
