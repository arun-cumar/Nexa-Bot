// © 2026 arun•°Cumar. All Rights Reserved.
import config from "../config.js";
import { getPrefix } from '../../lib/nexa/settings/ prefix.js';

export const parseMessage = (msg) => {
    const m = msg.message || {};
    
    const body =
        m.conversation ||
        m.extendedTextMessage?.text ||
        m.imageMessage?.caption ||
        m.videoMessage?.caption ||
        m.documentMessage?.caption ||
        m.buttonsResponseMessage?.selectedButtonId ||
        m.listResponseMessage?.singleSelectReply?.selectedRowId ||
        m.templateButtonReplyMessage?.selectedId ||
        m.interactiveResponseMessage?.nativeFlowResponseMessage?.paramsJson ||
        m.viewOnceMessage?.message?.imageMessage?.caption ||
        m.viewOnceMessage?.message?.videoMessage?.caption ||
        "";

    const text = body.trim();
    
    const dynamicPrefix = getPrefix(); 
    
    const prefixes = [...config.PREFIX.split(''), dynamicPrefix];

    const isCmd = prefixes.some(p => text.startsWith(p));
    
    const prefix = isCmd ? prefixes.find(p => text.startsWith(p)) : "";
    
    const commandName = isCmd ? text.slice(prefix.length).trim().split(/ +/)[0].toLowerCase() : "";
   
    const args = text.trim().split(/ +/).slice(1);
  
    const fullArgs = args.join(" ");

    const from = msg.key?.remoteJid;
    
    const isGroup = from?.endsWith("@g.us");
   
    const sender = isGroup ? msg.key?.participant : from;
  
    const pushName = msg.pushName || "User";

    const quoted = m.extendedTextMessage?.contextInfo?.quotedMessage ? {
        message: m.extendedTextMessage.contextInfo.quotedMessage,
        sender: m.extendedTextMessage.contextInfo.participant,
        id: m.extendedTextMessage.contextInfo.stanzaId,
        isMedia: !!(m.extendedTextMessage.contextInfo.quotedMessage.imageMessage || 
                   m.extendedTextMessage.contextInfo.quotedMessage.videoMessage || 
                   m.extendedTextMessage.contextInfo.quotedMessage.stickerMessage)
    } : null;

    const isMedia = !!(m.imageMessage || m.videoMessage || m.stickerMessage || m.documentMessage);
  
    const type = Object.keys(m)[0]; 

    return {
        body,
        text,
        isCmd,
        commandName,
        args,
        fullArgs,
        sender,
        pushName,
        from,
        isGroup,
        prefix,
        quoted,
        isMedia,
        type,
        msg
    };
};
