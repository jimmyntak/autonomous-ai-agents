import discord
import os

# Load token from environment variable
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
CHANNEL_ID = 1336863891702943755  # Replace with your channel ID
LOG_FILE_PATH = '/Users/jimmyntak/Desktop/NovibetoutputJimmy.log'

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

        # Ensure the log file exists
        if not os.path.isfile(LOG_FILE_PATH):
            print(f"Log file not found at {LOG_FILE_PATH}")
            await self.close()
            return

        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            await self.close()
            return

        # If the content is within Discord's limit, send it as one message.
        if len(content) <= MAX_MESSAGE_LENGTH:
            try:
                await channel.send(content)
                print("Log file sent as a single message.")
            except Exception as e:
                print(f"Failed to send message: {e}")
        else:
            print("Content exceeds Discord's message limit. Splitting into multiple messages.")
            # Split the content by lines and group them so that each message is under the limit.
            chunks = []
            current_chunk = ""
            for line in content.splitlines(keepends=True):
                if len(current_chunk) + len(line) > MAX_MESSAGE_LENGTH:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            # Append any remaining text as the last chunk.
            if current_chunk:
                chunks.append(current_chunk)

            # Send each chunk as a separate message.
            for idx, chunk in enumerate(chunks):
                try:
                    await channel.send(chunk)
                    print(f"Sent chunk {idx + 1} of {len(chunks)}")
                except Exception as e:
                    print(f"Failed to send message chunk {idx + 1}: {e}")
                    break

        # Close the bot once done.
        await self.close()

client = LogFileBot(intents=intents)
client.run(TOKEN)