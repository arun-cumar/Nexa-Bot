import stickerHandler from '../commands/sticker.js';
import aliveHandler from '../commands/alive.js';

export default async (commandName, sock, msg, args, extra) => {
    const { isOwner, isAdmin } = extra;

    if (commandName === 'menu' || commandName === 'help') {
        await menuHandler(sock, msg, args);
    } 
    
    else if (commandName === 'alive') {
        await aliveHandler(sock, msg);
    }
    
     else if (commandName === 'ping') {
        await pingHandler(sock, msg);
    }
     
     else if (commandName === 'url') {
        await urlHandler(sock, msg);
    }
         
    else {
        
        console.log(`Unknown command: ${commandName}`);
    }
};
