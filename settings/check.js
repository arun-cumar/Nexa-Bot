// © 2026 arun•°Cumar. All Rights Reserved.
import config from "../config.js";

export const checkAdmin = async (sock, from, sender) => {
    try {
        const groupMetadata = await sock.groupMetadata(from);
        const participants = groupMetadata.participants || [];
        const user = participants.find(p => p.id === sender);
        return user?.admin === 'admin' || user?.admin === 'superadmin';
    } catch (e) {
        return false;
    }
};

export const checkOwner = (sender, fromMe) => {
    const senderNumber = sender.replace(/\D/g, '');
    return config.OWNER_NUMBER.some(num => num.replace(/\D/g, '') === senderNumber) || fromMe;
};
