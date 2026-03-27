// © 2026 arun•°Cumar. All Rights Reserved.
import { calculate } from '../lib/calculate.js';

export default {
    name: 'math',
    category: 'tools',
    async execute(msg, sock, args) {
      
        if (args.length < 3) {
            return await sock.sendMessage(msg.chat, { text: "example: .math 10 + 5" });
        }

        const result = calculate(args[0], args[1], args[2]);
        
        await sock.sendMessage(m.chat, { 
            text: `📊 *RESULT:* ${args[0]} ${args[1]} ${args[2]} = *${result}*` 
        }, { quoted: msg });
    }
};
