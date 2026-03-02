const Discord = require("discord.js");
const fs = require('fs');
const date = require('date-and-time');
const readLastLines = require('read-last-lines');
const bot = new Discord.Client();
const now = new Date();

var settings = require("./settings.js");
var logFile = "/Users/jimmyntak/Downloads/blade/program/logs/status.log"; // Update to the log file you want to monitor
let logMessage; // To store the message we will edit later

bot.on("ready", async function () {
    console.log("ready");
    console.log("Stream ready - Starting live Playlist...." + date.format(now, 'DD/MM/YYYY'));
    logMessage = await bot.channels.cache.get(settings.discord_channel).send("Stream ready - Starting live Playlist...." + date.format(now, 'DD/MM/YYYY') + "\nFetching log content...");

    // Read the initial last 50 lines and send it in the message
    updateLogContent();
});

fs.watchFile(logFile, async (eventType, filename) => {
    // Update log content when the file changes
    updateLogContent();
});

async function updateLogContent() {
    try {
        // Read the last 50 lines of the log file
        const lines = await readLastLines.read(logFile, 50);

        // Split the lines into individual lines and extract the part after the 4th hyphen
        const filteredLines = lines
            .split('\n') // Split the content into individual lines
            .map(line => {
                const parts = line.split(' - '); // Split each line by ' - '
                return parts.length >= 5 ? parts[4] : ''; // Return the part after the 4th hyphen, if exists
            })
            .filter(Boolean) // Remove any empty lines (in case the split doesn't have enough parts)
            .join('\n'); // Join the filtered lines back into a single string

        // Check if the filtered lines exceed 2000 characters
        if (filteredLines.length > 2000) {
            // Truncate the content to fit within the 2000-character limit
            const truncatedLines = filteredLines.substring(filteredLines.length - 2000); // Take the last 2000 characters
            console.log("Message truncated to 2000 characters.");

            // Edit the message with the truncated lines
            if (logMessage) {
                await logMessage.edit("Stream ready - Live Log (truncated):\n" + "```" + truncatedLines + "```");
            }
        } else {
            // Edit the message with the filtered lines
            if (logMessage) {
                await logMessage.edit("Live Status Log:\n" + "```" + filteredLines + "```");
            }
        }
    } catch (error) {
        console.error("Error reading log file: ", error);
    }
}

bot.login(settings.bot_token);