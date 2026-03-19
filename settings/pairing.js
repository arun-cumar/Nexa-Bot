import chalk from 'chalk';
import readline from 'readline';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (text) => new Promise((resolve) => rl.question(text, resolve));
export async function handlePairing(sock) {
    console.clear();
    console.log(
        chalk.redBright(` Nexa-Bot 
        PAIRING MODE `)
    );

    if (!sock.authState.creds.registered) {

        //  Input Section
        const phoneNumber = await question(
            chalk.redBright('📞 Enter Phone Number: ') +
            chalk.gray('(eg: 91XXXXXXXXXX) ➤ ')
        );

        const cleanNumber = phoneNumber.replace(/[^0-9]/g, '');

        console.log(
            chalk.red('\n⏳ Generating secure pairing code...\n')
        );

        //  Pairing Code
        const code = await sock.requestPairingCode(cleanNumber);

        // 🎯 Output Box
        console.log(
            chalk.redBright(`
       🗝 YOUR PAIRING CODE         
           ${code} `)
        );

        console.log(
            chalk.gray('⚡ Use this code in WhatsApp to link your device\n')
        );
    }

    rl.close();
  }
