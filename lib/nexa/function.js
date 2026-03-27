// © 2026 arun•°Cumar. All Rights Reserved.

// Runtime 
export const runtime = (seconds) => {
    seconds = Number(seconds);
    var d = Math.floor(seconds / (3600 * 24));
    var h = Math.floor(seconds % (3600 * 24) / 3600);
    var m = Math.floor(seconds % 3600 / 60);
    var s = Math.floor(seconds % 60);

    var dDisplay = d > 0 ? d + (d == 1 ? " day, " : " days, ") : "";
    var hDisplay = h > 0 ? h + (h == 1 ? " hour, " : " hours, ") : "";
    var mDisplay = m > 0 ? m + (m == 1 ? " minute, " : " minutes, ") : "";
    var sDisplay = s > 0 ? s + (s == 1 ? " second" : " seconds") : "";

    return dDisplay + hDisplay + mDisplay + sDisplay;
};

// Random  Designs
export const timeDesigns = [
`╭━━━〔 NEXA BOT 〕━━━╮
┃ 👤 User: {user}
┃ ⏱ Uptime: {uptime}
┃ 📅 Date: {date}
┃ ⌚ Time: {time}
┃ 🛡 Status: Online
╰━━━━━━━━━━━━━━━╯`,

`✨ *NEXA BOT MD* ✨
👤 User: {user}
⏱ Uptime: {uptime}
📅 {date}
⌚ {time}
🚀 System Running Perfectly`,

`🤖 NEXA BOT ACTIVE
━━━━━━━━━━━━━━
👤 {user}
⏱ {uptime}
📅 {date}
⌚ {time}
━━━━━━━━━━━━━━`,
`╔═════════════════╗
║       NEXA BOT      ║
╠══════════════════╣
║ 👤 User   : {user}
║ ⏱ Uptime : {uptime}
║ 📅 Date   : {date}
║ ⌚ Time   : {time}
║ 🛡 Status : Online
╚═════════════════╝`,

`╭────────────╮
│     *NEXA BOT MD*         
│ 👤 User   : {user}
│ ⏱ Uptime : {uptime}
│ 📅 Date   : {date}
│ ⌚ Time   : {time}
│ 🚀 Running Smoothly
╰─────────────╯`,

`┏━━━━━━━━━━━━┓
┃     NEXA BOT       ┃
┣━━━━━━━━━━━━━┫
┃ 👤 User   : {user}
┃ ⏱ Uptime : {uptime}
┃ 📅 Date   : {date}
┃ ⌚ Time   : {time}
┃ ⚡ System Online
┗━━━━━━━━━━━━━┛`,

`╔══〔 NEXA BOT MD 〕══╗
║ 👤 User   : {user}
║ ⏱ Uptime : {uptime}
║ 📅 Date   : {date}
║ ⌚ Time   : {time}
║ 🤖 Bot Active & Ready
╚═══════════════════╝`,

`〔 NEXA BOT SYSTEM 〕
│ 👤 User   : {user}
│ ⏱ Uptime : {uptime}
│ 📅 Date   : {date}
│ ⌚ Time   : {time}
│ 🛡 Protection Enabled`,

`┌─────────────────┐
│     NEXA BOT MD     │
├──────────────────┤
│ 👤 User   : {user}
│ ⏱ Uptime : {uptime}
│ 📅 Date   : {date}
│ ⌚ Time   : {time}
│ ⚡ Bot Running
└──────────────────┘`,

`╔━━━━━━━━━━━━━╗
║   🤖 NEXA BOT 🤖     ║
╠━━━━━━━━━━━━━━╣
║ 👤 User   : {user}
║ ⏱ Uptime : {uptime}
║ 📅 Date   : {date}
║ ⌚ Time   : {time}
║ 🚀 Online Mode
╚━━━━━━━━━━━━━━╝`,

`╭━━━━━━━━━━━━━╮
┃     NEXA BOT MD     ┃
┣━━━━━━━━━━━━━┫
┃ 👤 User   : {user}
┃ ⏱ Uptime : {uptime}
┃ 📅 Date   : {date}
┃ ⌚ Time   : {time}
┃ 🔥 Fully Active
╰━━━━━━━━━━━━╯`,

`┏━━━〔 NEXA BOT 〕━━━┓
┃ 👤 User   : {user}
┃ ⏱ Uptime : {uptime}
┃ 📅 Date   : {date}
┃ ⌚ Time   : {time}
┃ ⚙️ System Working
┗━━━━━━━━━━━━━━━┛`,

`╔══════════════════════╗
║        NEXA BOT MD        ║
╠═══════════════════════╣
║ 👤 User   : {user}
║ ⏱ Uptime : {uptime}
║ 📅 Date   : {date}
║ ⌚ Time   : {time}
║ 🌐 Connected Successfully
╚═══════════════════════╝`
];
