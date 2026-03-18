import fs from "fs";
import path from "path";

const toggleFile = "./media/toggles.json";
const pluginsFolder = "./plugins";

// Get saved toggles
export const getToggles = () => {
    if (fs.existsSync(toggleFile)) {
        return JSON.parse(fs.readFileSync(toggleFile));
    }
    return {};
};

// Save toggles
export const saveToggles = (toggles) => {
    fs.writeFileSync(toggleFile, JSON.stringify(toggles, null, 2));
};

// Scan plugins and create toggle list
export const generateTogglesFromPlugins = async () => {
    const files = fs.readdirSync(pluginsFolder).filter(f => f.endsWith(".js"));

    let toggles = getToggles();

    for (const file of files) {
        try {
            const pluginPath = path.resolve(`${pluginsFolder}/${file}`);
            const plugin = await import(pluginPath);

            const commandName = plugin.default?.name || file.replace(".js", "");

            // Default values
            if (!toggles[commandName]) {
                toggles[commandName] = {
                    status: "on",      // on / off
                    mode: "public"     // public / private
                };
            }

        } catch (err) {
            console.log(`Error loading plugin: ${file}`, err);
        }
    }

    saveToggles(toggles);
    return toggles;
};
