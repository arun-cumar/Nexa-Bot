// © 2026 arun•°Cumar. All Rights Reserved.
import ownerHandler from '../plugins/system/owner.js';
import menuHandler from '../plugins/system/menu.js';
import aliveHandler from '../plugins/system/alive.js';
import pingHandler from '../plugins/system/ping.js';
import uptimeHandler from '../plugins/system/uptime.js';
import urlHandler from '../plugins/download/url.js';
import stickerHandler from '../plugins/edit/sticker.js';
import videoHandler from '../plugins/download/video.js';
import playHandler from '../plugins/download/play.js';
import tagallHandler from '../plugins/group/tagall.js';
import mathHandler from '../plugins/genaral/math.js';
import restartHandler from '../plugins/system/restart.js';
import prefixHandler from '../plugins/system/prefix.js';
import vvHandler from '../plugins/utility/vv.js';
// map
const commands = {
    menu: menuHandler,
    help: menuHandler,
    owner: ownerHandler,
    alive: aliveHandler,
    ping: pingHandler,
    uptime: uptimeHandler,
    runtime: uptimeHandler,
    url: urlHandler,
    link: urlHandler,
    sticker: stickerHandler,
    s: stickerHandler,
    video: videoHandler,
    play: playHandler,
    song: playHandler,
    tagall: tagallHandler,
    math: mathHandler,
    calculate: mathHandler,
    restart: restartHandler,
    update: restartHandler,
    prefix: prefixHandler,
    setprefix: prefixHandler,
    vv: vvHandler,
    viewOnce: vvHandler 
};

// handler
export async function handleCommands(commandName, sock, msg, args, extra) {
    try {
        if (commands[commandName]) {
            await commands[commandName](sock, msg, args, extra);
        } else {
            console.log("Unknown command:", commandName);
        }
    } catch (err) {
        console.log("Command Error:", err);
    }
}
