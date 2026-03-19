import path from "path";
import { pathToFileURL } from "url";
import fs from "fs";

export const executeCommand = async (commandName, sock, msg, args, extra) => {
    
    const safeCommandName = path.basename(commandName);
    const commandPath = path.join(process.cwd(), "plugins", `${safeCommandName}.js`);

    try {
        
        if (!fs.existsSync(commandPath)) {
            return false;
        }

        const moduleUrl = `${pathToFileURL(commandPath).href}?update=${Date.now()}`;
        const commandModule = await import(moduleUrl);

        const handler = commandModule.default || commandModule.run || commandModule.execute;

        if (typeof handler === "function") {
            
            await Promise.race([
                handler(sock, msg, args, extra),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error("Command Timeout")), 15000)
                )
            ]);
            return true;
        }

        console.warn(`[Warning]: Command ${safeCommandName} has no valid export function.`);
        return false;

    } catch (err) {
        // 6. Detailed Error Logging without crashing the main process
        console.error(`[Command Error] -> "${commandName}":`, err.message);
        
        return false;
    }
};

