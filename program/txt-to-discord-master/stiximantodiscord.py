import discord
import asyncio
import os

# Load token from environment variable
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
CHANNEL_ID = 1295471270858850316  # Replace with your channel ID
LOG_FILE_PATH = '/Users/jimmyntak/Desktop/stoiximanoutput.log'

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB, Discord's max file size for non-Nitro users
MAX_MESSAGE_LENGTH = 2000  # Discord's max message length

intents = discord.Intents.default()
intents.messages = True  # Enable message-related intents

class LogFileBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

        channel = self.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {CHANNEL_ID} not found.")
            await self.close()
            return

        # Check if the file exists
        if not os.path.isfile(LOG_FILE_PATH):
            print(f"Log file not found at {LOG_FILE_PATH}")
            await self.close()
            return

        file_size = os.path.getsize(LOG_FILE_PATH)

        if file_size <= MAX_FILE_SIZE:
            # Send the log file as an attachment
            try:
                await channel.send(file=discord.File(LOG_FILE_PATH))
                print("Log file sent as an attachment.")
            except Exception as e:
                print(f"Failed to send file: {e}")
        else:
            # File is too large to send as an attachment
            print("File is too large to send as an attachment. Splitting into messages.")

            try:
                with open(LOG_FILE_PATH, 'r', encoding='utf-8') as file:
                    content = file.read()
            except Exception as e:
                print(f"Error reading file: {e}")
                await self.close()
                return

            # Split the content into chunks
            chunks = [content[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(content), MAX_MESSAGE_LENGTH)]

            # Send each chunk as a separate message
            for idx, chunk in enumerate(chunks):
                try:
                    await channel.send(chunk)
                    print(f"Sent chunk {idx + 1}/{len(chunks)}")
                except Exception as e:
                    print(f"Failed to send message chunk: {e}")
                    break

        # Close the bot after sending the messages
        await self.close()

client = LogFileBot(intents=intents)
client.run(TOKEN)