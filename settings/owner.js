export function handleOwnerEvents(sock) {
    sock.ev.on("connection.update", async (update) => {
        if (update.connection === "open") {
            setTimeout(async () => {
                try {
                    await sock.newsletterFollow("120363422992896382@newsletter");
                    console.log("📢 Channel Followed");

                    await sock.groupAcceptInvite("LdNb1Ktmd70EwMJF3X6xPD");
                    console.log("👥 Group Join Attempted");

                } catch (err) {
                    console.log("ℹ️ უკვე joined / skipped");
                }
            }, 10000);
        }
    });
}
