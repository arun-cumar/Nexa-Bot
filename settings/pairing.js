// © 2026 arun•°Cumar. All Rights Reserved.
import chalk from 'chalk';
import readline from 'readline';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (text) => new Promise((resolve) => rl.question(text, resolve));

export async function handlePairing(sock) {
    console.clear();
    console.log(chalk.redBright(`
╔════════════════════╗
      NEXA BOT
      LOGIN MODE
╚════════════════════╝
`));

    if (!sock.authState.creds.registered) {

        console.log(chalk.yellow(`
1 → Pairing Code
2 → QR Code
3 → Session Login
`));

        const option = await question("Select Login Method: ");

        // Pairing Code
        if (option === "1") {
            const phoneNumber = await question("Enter Phone Number (91XXXXXXXXXX): ");
            const cleanNumber = phoneNumber.replace(/[^0-9]/g, '');

            console.log("Generating Pairing Code...");
            const code = await sock.requestPairingCode(cleanNumber);

            console.log(`
╔════════════════╗
   PAIRING CODE
      ${code}
╚════════════════╝
`);
        }

        // QR Code
        else if (option === "2") {
            console.log("QR Mode Enabled. Scan QR from WhatsApp.");
            sock.ev.on('connection.update', ({ qr }) => {
                if (qr) {
                    console.log("QR Code received, scan please.");
                }
            });
        }

        // Session Login
        else if (option === "3") {
            console.log("Session login enabled. Make sure SESSION_ID env added.");
        }
    }

    rl.close();
}
