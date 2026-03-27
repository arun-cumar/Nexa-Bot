// © 2026 arun•°Cumar. All Rights Reserved.
export const getRandomPing = (ping, speedStatus, netStatus) => {
    const messages = [
        `🚀 *Speed:* ${speedStatus}
        📡 *Latency:* ${ping} ms
        📶 *Network:* ${netStatus}`,
        
        `⚡ *System Status:* Online
        📟 *Ping:* ${ping} ms
        🛰️ *Connection:* Stable`,
        
        `🤖 *NEXA-BOT Response:* ${ping} ms
        🔥 *Mode:* Turbo
        🌐 *Server:* Active`,
        
        `📡 *Scanning Network...*
        ⏱️ *Time:* ${ping} ms
        ✅ *Status:* All systems go!`,
        
        `🛰️ *Ping:* ${ping} ms
        📊 *Efficiency:* 100%
        🔋 *Power:* Optimal`,
        
        `🌀 *Latency:* ${ping} ms
        📍 *Region:* Global
        💎 *Quality:* High`,
        
        `🚀 *NEXA Engine:* Running
        ⏱️ *Delay:* ${ping} ms
        🛠️ *Maintenance:* None`,
        
        `📡 *Signal:* Strong
        📟 *Ping:* ${ping} ms
        🌟 *Experience:* Smooth`,
        
        `⚡ *Current Speed:* ${speedStatus}
        🕒 *Latency:* ${ping} ms
        🌈 *Nexa Style: Active*`,
        
        `🛰️ *Direct Link:* Established
        📟 *Ping:* ${ping} ms
        🛡️ *Security:* Secure`
    ];

    return messages[Math.floor(Math.random() * messages.length)];
};
