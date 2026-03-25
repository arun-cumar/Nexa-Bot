// © 2026 arun•°Cumar. All Rights Reserved.
import { fquoted } from './quoted.js'; 
import menuHandler from '../plugins/menu.js';
import aliveHandler from '../plugins/alive.js';
import pingHandler from '../plugins/ping.js';
import urlHandler from '../plugins/url.js';
import stickerHandler from '../plugins/sticker.js';

export async function executeCommand(commandName, sock, msg, args, extra) {
    const { isOwner, isAdmin } = extra;
}

    const quoted = fquoted(msg); 

    if (commandName === 'menu' || commandName === 'help') {
        
        await menuHandler(sock, msg, args, { isOwner, isAdmin, quoted });
    } 
    
    else if (commandName === 'alive') {
        await aliveHandler(sock, msg, args, { isOwner, isAdmin, quoted });
    }
    
    else if (commandName === 'ping') {
        await pingHandler(sock, msg, args, { isOwner, isAdmin, quoted });
    }
     
    else if (commandName === 'url' || commandName === 'link') {
        await urlHandler(sock, msg, args, { isOwner, isAdmin, quoted });
    }

    else if (commandName === 'sticker' || commandName === 's') {
        await stickerHandler(sock, msg, args, { isOwner, isAdmin, quoted });
    }
    
    else {
        console.log(`Unknown command: ${commandName}`);
    }
}; 
