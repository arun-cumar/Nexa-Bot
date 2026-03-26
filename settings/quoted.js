
import fs from 'fs';
import { fileURLToPath } from 'url';
import chalk from 'chalk'; 

export const getQuoted = (msg) => {
    return {
        key: {
            fromMe: false,
            participant: "0@s.whatsapp.net",
            remoteJid: "status@broadcast" 
        },
        message: {
            newsletterAdminInviteMessage: {
                newsletterJid: "120363422992896382@newsletter",
                newsletterName: "⚡NEXA-BOT-MD OFFICIAL",
                caption: "🚀 NEXA-BOT-MD : THE NEXT GEN BOT",
                inviteExpiration: Date.now() + 1800000,
                jpegThumbnail: fs.readFileSync('./media/nexa.jpg') 
            }
        }
    };
};

const __filename = fileURLToPath(import.meta.url);
fs.watchFile(__filename, () => {
    fs.unwatchFile(__filename);
    console.log(chalk.redBright('─╼[ ') + chalk.white('File Updated: ') + chalk.greenBright(__filename.split('/').pop()) + chalk.redBright(' ]╾─'));
});
