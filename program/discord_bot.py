import os
import discord
from discord.ext import commands
from thread_manager import trigger_event, run_threads

from config_manager import ConfigManager
from logger_config import status_logger  # Εισαγωγή του status_logger

class DiscordBot:
    def __init__(self, config_path):
        # Φόρτωση των ρυθμίσεων από το config file
        self.config_manager = ConfigManager(config_path)
        discord_config = self.config_manager.get_discord_config()

        # Αποθήκευση των ρυθμίσεων ως μέλη της κλάσης
        self.channel_id = discord_config.channel_id
        self.bot_token = discord_config.bot_token
        self.keywords = discord_config.keywords
        self.image_download_path = discord_config.image_download_path

        # Δημιουργία του bot με command prefix
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)

        # Σύνδεση των event handlers
        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)

    async def on_ready(self):
        status_logger.info(f'Logged in as {self.bot.user}')

    async def on_message(self, message):
        if message.channel.id != self.channel_id:
            return
        status_logger.info(f"{message.author}: {message.content}")

        # Έλεγχος για τις λέξεις-κλειδιά στο μήνυμα
        for keyword in self.keywords:
            if keyword in message.content:
                status_logger.info(f'The bet is "{keyword}!"')
                # Αν το μήνυμα περιέχει συνημμένα αρχεία
                for attachment in message.attachments:
                    if attachment.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                        save_path = os.path.join(self.image_download_path, f"latest_photo_{attachment.filename}")
                        await self.save_attachment(attachment, save_path, keyword)
                break

        # Προσθέτουμε το on_message event στη βάση του bot
        await self.bot.process_commands(message)


    async def save_attachment(self, attachment, save_path, keyword):
        with open(save_path, "wb") as f:
            await attachment.save(f)
            status_logger.info(f"Αποθηκεύτηκε η τελευταία φωτογραφία '{save_path}'")
            trigger_event(save_path, keyword)

    def run(self):
        # Εκκίνηση του bot
        self.bot.run(self.bot_token)

if __name__ == "__main__":
    # Ορίστε τη διαδρομή για το config αρχείο
    config_path = '/Users/jimmyntak/Downloads/blade/config/config.json'
    run_threads()

    # Δημιουργία instance του DiscordBot και εκκίνηση του bot
    discord_bot = DiscordBot(config_path)
    discord_bot.run()

