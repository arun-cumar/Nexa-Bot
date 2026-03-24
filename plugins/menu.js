// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import path from 'path';
import config from '../config.js';
import menuDesigns from '../lib/menu.js';
import { sendInteractiveMessage } from '../settings/interactive.js';

export default async (sock, msg, args) => {
    try {
        const from = msg.key.remoteJid;
        
        const sender = msg.key.participant || from;
        
        const pushName = msg.pushName || "User";

        // Runtime / Uptime
        const runtime = process.uptime();
        
        const hours = Math.floor(runtime / 3600);
        
        const minutes = Math.floor((runtime % 3600) / 60);
        
        const seconds = Math.floor(runtime % 60);
        
        const uptime = `${hours}h ${minutes}m ${seconds}s`;

        // Date & Time
        const date = new Date().toLocaleDateString();
        
        const time = new Date().toLocaleTimeString();
        
        // Commands Read
        const commandsDir = path.join(process.cwd(), 'plugins);
                                      
        const files = fs.readdirSync(commandsDir).filter(file => file.endsWith('.js'));

        // Command List Create
        let commandList = '';
        
        let totalCommands = 0;

        files.forEach((file, index) => {
            
            const cmdName = file.replace('.js', '');
            
            totalCommands++;
            
            commandList += `${index + 1}. ${config.PREFIX}${cmdName}\n`;
        });

        // Random Menu Design
        const randomDesign = menuDesigns[Math.floor(Math.random() * menuDesigns.length)];

        const menuText = randomDesign
            .replace('{bot}', config.BOT_NAME)
            .replace('{user}', pushName)
            .replace('{date}', date)
            .replace('{time}', time)
            .replace('{uptime}', uptime)
            .replace('{total}', totalCommands)
            .replace('{prefix}', config.PREFIX)
            .replace('{commands}', commandList);

        // Interactive Buttons
        const buttons = [
            {
                name: "quick_reply",
                buttonParamsJson: JSON.stringify({
                    display_text: "⚡ Ping",
                    id: `${config.PREFIX}ping`
                })
            },
            {
                name: "quick_reply",
                buttonParamsJson: JSON.stringify({
                    display_text: "🟢 Alive",
                    id: `${config.PREFIX}alive`
            
                })
            }
        ];

        // Send Interactive Menu
        await sendInteractiveMessage(sock, from, {
            text: menuText,
            footer: `© ${config.BOT_NAME}`,
            buttons: buttons
        }, { quoted: msg });

    } catch (err) {
        console.log("Menu Error:", err);
    }
};
