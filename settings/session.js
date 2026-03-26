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
    console.log(chalk.cyan(`
    ╔══════════════════════════════════════╗
    ║          🚀 NEXA BOT SYSTEM          ║
    ║        Developed by arun•°Cumar      ║
    ╚══════════════════════════════════════╝
    `));

    if (!sock.authState.creds.registered) {
        console.log(chalk.whiteBright('   [ SELECT LOGIN METHOD ]\n'));
        console.log(chalk.green('   1 ➤ ') + chalk.white('Pairing Code (Easy)'));
        console.log(chalk.green('   2 ➤ ') + chalk.white('QR Code (Fast Scan)'));
        console.log(chalk.green('   3 ➤ ') + chalk.white('Session ID (Auto Login)\n'));

        const option = await question(chalk.cyan('   ⚡ Select Option: '));

        // 1. Pairing Code Mode
        if (option === "1") {
            const phoneNumber = await question(chalk.yellow('\n   📞 Enter Number (91XXXXXXXXXX): '));
            const cleanNumber = phoneNumber.replace(/[^0-9]/g, '');

            if (cleanNumber.length < 10) {
                console.log(chalk.red('   ❌ Invalid Phone Number!'));
                rl.close();
                return;
            }

            console.log(chalk.blue('   ⏳ Requesting Pairing Code...'));
            try {
                const code = await sock.requestPairingCode(cleanNumber);
                console.log(chalk.greenBright(`
    ╔══════════════════════════════════════╗
    ║        🗝  YOUR PAIRING CODE                ║
    ╠══════════════════════════════════════╣
    ║                 ${code}                     ║
    ╚══════════════════════════════════════╝
                `));
                console.log(chalk.gray('   💡 Open WhatsApp > Linked Devices > Link with Phone Number\n'));
            } catch (err) {
                console.log(chalk.red('   ❌ Error: ' + err.message));
            }
        }

        // 2. QR Code Mode
        else if (option === "2") {
            console.log(chalk.magenta('\n   📡 QR Mode Activated. Wait for QR to load...'));
            
        }

        // 3. Session Login
        else if (option === "3") {
            console.log(chalk.blue('\n   🔑 Checking Session ID from Environment...'));
            
        }
        
        else {
            console.log(chalk.red('\n   ❌ Invalid Option! Please restart.'));
        }
    }

    rl.close();
}
