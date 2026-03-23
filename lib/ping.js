export const getRandomPing = (ping, speedStatus, netStatus) => {
    const messages = [
        `🚀 *Speed:* ${speedStatus}\n📡 *Latency:* ${ping} ms\n📶 *Network:* ${netStatus}`,
        `⚡ *System Status:* Online\n📟 *Ping:* ${ping} ms\n🛰️ *Connection:* Stable`,
        `🤖 *NEXA-BOT Response:* ${ping} ms\n🔥 *Mode:* Turbo\n🌐 *Server:* Active`,
        `📡 *Scanning Network...*\n⏱️ *Time:* ${ping} ms\n✅ *Status:* All systems go!`,
        `🛰️ *Ping:* ${ping} ms\n📊 *Efficiency:* 100%\n🔋 *Power:* Optimal`,
        `🌀 *Latency:* ${ping} ms\n📍 *Region:* Global\n💎 *Quality:* High`,
        `🚀 *NEXA Engine:* Running\n⏱️ *Delay:* ${ping} ms\n🛠️ *Maintenance:* None`,
        `📡 *Signal:* Strong\n📟 *Ping:* ${ping} ms\n🌟 *Experience:* Smooth`,
        `⚡ *Current Speed:* ${speedStatus}\n🕒 *Latency:* ${ping} ms\n🌈 *Nexa Style: Active*`,
        `🛰️ *Direct Link:* Established\n📟 *Ping:* ${ping} ms\n🛡️ *Security:* Secure`
    ];

    return messages[Math.floor(Math.random() * messages.length)];
};
