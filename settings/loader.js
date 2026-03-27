// © 2026 arun•°Cumar. All Rights Reserved.   
import ownerHandler from '../plugins/system/owner.js';
import menuHandler from '../plugins/system/menu.js';  
import aliveHandler from '../plugins/system/alive.js';  
import pingHandler from '../plugins/system/ping.js'; 
import uptimeHandler from '../plugins/system/uptime.js';
import urlHandler from '../plugins/download/url.js';  
import stickerHandler from '../plugins/download/sticker.js';  
import videoHandler from '../plugins/download/video.js';  
import playHandler from '../plugins/download/play.js';  
import tagallHandler from '../plugins/group/tagall.js';

export async function handleCommands(commandName, sock, msg, args, extra) {  
    const { isOwner, isAdmin } = extra;  
  
    // commands checking 
    switch (commandName) {
        case 'menu':
        case 'help':
            await menuHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'owner':
            await ownerHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'alive':
            await aliveHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'ping':
            await pingHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'uptime':
        case 'runtime':
            await uptimeHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'url':
        case 'link':
            await urlHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'sticker':
        case 's':
            await stickerHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'video':
            await videoHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'play':
        case 'song':
            await playHandler(sock, msg, args, { isOwner, isAdmin });
            break;

        case 'tagall':
            await tagallpHandler(sock, msg, args, { isOwner, isAdmin });
            break;
            
        default:
            console.log(`Unknown command: ${commandName}`);
            break;
    }
}
