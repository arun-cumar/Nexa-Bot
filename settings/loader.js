// © 2026 arun•°Cumar. All Rights Reserved.
import { fquoted } from './settings/quoted.js';
import menuHandler from '../plugins/menu.js';
import aliveHandler from '../plugins/alive.js';
import pingHandler from '../plugins/ping.js';
import urlHandler from '../plugins/url.js';
import stickerHandler from '../plugins/sticker.js';

export default async (commandName, sock, msg, args, extra) => {
    const { isOwner, isAdmin } = extra;

    if (commandName === 'menu' || commandName === 'help') {
        await menuHandler(sock, msg, args, fquoted);
    } 
    
    else if (commandName === 'alive') {
        await aliveHandler(sock, msg, args, fquoted);
    }
    
     else if (commandName === 'ping') {
        await pingHandler(sock, msg, args, fquoted);
    }
     
     else if (commandName === 'url') {
        await urlHandler(sock, msg, args, fquoted);
    }

    else if (commandName === 'url') {
        await urlHandler(sock, msg, args, fquoted);
    }

    else if (commandName === 'sticker') {
        await stickerHandler(sock, msg, args, fquoted);
    }
        
        console.log(`Unknown command: ${commandName}`);
    }
};
