// © 2026 arun•°Cumar. All Rights Reserved.
export const sendInteractiveMessage = async (sock, from, opts = {}) => {
    const {
        title,
        body,
        footer,
        buttons = [],
        sections = [],
        media = null,
        viewOnce = true
    } = opts;

    let formattedButtons = [];

    // Quick Reply Buttons
    buttons.forEach(btn => {
        if (btn.type === "reply") {
            formattedButtons.push({
                name: 'quick_reply',
                buttonParamsJson: JSON.stringify({
                    display_text: btn.displayText,
                    id: btn.id
                })
            });
        }

        // URL Button
        if (btn.type === "url") {
            formattedButtons.push({
                name: 'cta_url',
                buttonParamsJson: JSON.stringify({
                    display_text: btn.displayText,
                    url: btn.url
                })
            });
        }

        // Copy Button
        if (btn.type === "copy") {
            formattedButtons.push({
                name: 'cta_copy',
                buttonParamsJson: JSON.stringify({
                    display_text: btn.displayText,
                    copy_code: btn.code
                })
            });
        }
    });

    // List Sections
    let sectionData = [];
    if (sections.length > 0) {
        sectionData = sections.map(sec => ({
            title: sec.title,
            rows: sec.rows.map(row => ({
                title: row.title,
                description: row.description,
                id: row.id
            }))
        }));

        formattedButtons.push({
            name: 'single_select',
            buttonParamsJson: JSON.stringify({
                title: "Select Option",
                sections: sectionData
            })
        });
    }

    let header = { title: title };

    // Media Header
    if (media) {
        header = {
            hasMediaAttachment: true,
            ...media
        };
    }

    const message = {
        viewOnceMessage: {
            message: {
                interactiveMessage: {
                    header,
                    body: { text: body },
                    footer: { text: footer },
                    nativeFlowMessage: {
                        buttons: formattedButtons
                    }
                }
            }
        }
    };

    await sock.sendMessage(from, message);
};
