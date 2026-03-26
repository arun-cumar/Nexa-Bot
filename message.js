// © 2026 arun•°Cumar. All Rights Reserved.
import path from "path";
import { pathToFileURL } from "url";
import fs from "fs";
import { checkAdmin, checkOwner } from "./settings/check.js";
import { getToggles } from "./lib/toggles.js";
import { parseMessage } from "./settings/msgHelper.js";
import { handleCommands } from "./settings/loader.js";
import { handleMentionSticker } from "./settings/mention.js";
import config from "./config.js";

export default async (sock, chatUpdate) => {
    try {
        const msg = chatUpdate.messages?.[0];
        if (!msg || !msg.message || msg.key.remoteJid === "status@broadcast") return;

        const from = msg.key.remoteJid;
        const isGroup = from.endsWith('@g.us');
        const sender = msg.key.participant || msg.key.remoteJid;
        const senderNumber = sender.replace(/\D/g, ''); 

        //  Owner checking
        const isOwner = checkOwner(sender, msg.key.fromMe);
        let isAdmin = false;
        if (isGroup) {
            isAdmin = await checkAdmin(sock, from, sender);
       }

        //  Mention Sticker Logic
        handleMentionSticker(sock, msg, from);
        
        // Parse Message    
        const { isCmd, commandName, args } = parseMessage(msg);    
        if (!isCmd || !commandName) return;    

        //  Get Toggles & Command Status Check
        const toggles = getToggles();    
        if (toggles[commandName]?.status === "off") return;    

        //  Global Public/Private Mode Check   
        if (global.isPublic === false && !isOwner) return;  

        //  Specific Command Private Check   
        if (toggles[commandName]?.mode === "private" && !isOwner) {  
            return await sock.sendMessage(from, { text: "🔒 This command is for my Owner only." });  
        }  

           // Execute commands 
        if (isCmd && commandName) {
            if (!from.endsWith('@lid')) {
                await sock.sendPresenceUpdate('composing', from);
            }
            
            await handleCommands(commandName, sock, msg, args, { isOwner, isAdmin });
        }

    } catch (err) {    
        console.error("❌ Message Error:", err);    
    }
};








