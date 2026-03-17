import path from "path";
import { pathToFileURL } from "url";
import fs from "fs";
import { getToggles, saveToggles } from "./lib/toggles.js";
import { parseMessage } from "./lib/msgHelper.js";
import { checkMode } from "./lib/mode.js";
import { executeCommand } from "./lib/loader.js";
import config from "./config.js";

export default async (sock, chatUpdate) => {
    try {
        const msg = chatUpdate.messages?.[0];
        if (!msg || !msg.message || msg.key.remoteJid === "status@broadcast") return;

        const from = msg.key.remoteJid;
        const sender = msg.key.participant || msg.key.remoteJid;
        const toggles = getToggles();

        // Parse Message
        const { isCmd, commandName, args } = parseMessage(msg);

        //  Mode Check
        if (!checkMode(sender, toggles)) return;

        //  Mode Command handling
        if (commandName === "mode") {
            const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]);
            if (!isOwner) return; 

            const newMode = args[0]?.toLowerCase();
            if (newMode === "public" || newMode === "private") {
                if (!toggles.global) toggles.global = {};
                toggles.global.mode = newMode;
                saveToggles(toggles);
                return await sock.sendMessage(from, { text: `✅ Mode: *${newMode}*` }, { quoted: msg });
            }
        }

        if (!isCmd) return;

        //  Command Execution (Loader)
         await executeCommand(commandName, sock, msg, args, { toggles });
                
    } catch (err) {
        console.error("Message Error:", err);
    }
};
