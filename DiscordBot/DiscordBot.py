"""
Discord bot for monitoring the status of the cam2lapse cameras.

Temporary solution until I can get a proper monitoring system set up.

In order to stop tracking a camera, the .webp file for that camera must be deleted. This will be fixed in the future.
"""
import asyncio
import os
import datetime
import discord
from pathlib import Path

# Load the Discord token from the environment
token = os.environ.get('DISCORD_TOKEN')

# How long to wait before sending a warning or error
warn_when = datetime.timedelta(minutes=30)
error_when = datetime.timedelta(hours=6)
# How long to wait between checking for new images
interval_min = 30

# Create the Discord client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True


def load_channel_ids() -> list:
    """Load the channel IDs from the file."""
    if not os.path.exists('channels.txt'):
        return []

    with open('channels.txt', 'r') as f:
        return [int(channel_id) for channel_id in f.read().split('\n') if channel_id]


def save_channel_ids() -> None:
    """Save the channel IDs to the file."""
    with open('channels.txt', 'w+') as f:
        converted = [str(channel_id) for channel_id in channel_ids]
        f.write('\n'.join(converted) + '\n')


channel_ids = load_channel_ids()
status = {}


class Cam2LapseBot(discord.Client):
    async def check_images(self):
        """Check the root directory for last modified date of .webp images."""
        for file in Path('img').glob('*.webp'):
            # Add file to status if it doesn't exist
            if file.name not in status:
                status[file.name] = 0

            time_elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(file.stat().st_mtime)

            if time_elapsed > error_when:
                await self.send_error(file.name.split('.webp')[0])
            elif time_elapsed > warn_when:
                status[file.name] += 1
                await self.send_warning(file.name.split('.webp')[0])
            else:
                status[file.name] = 0

    async def send_warning(self, camera_name: str):
        """Send a warning to all connected channels."""
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = f'Warning: Camera feed "{camera_name}" has not sent an update in a while.'
            text = f'This is warning #{status[camera_name]}.'
            embed = discord.Embed(title=title, description=text, color=0xff0000)
            await channel.send(embed=embed)
            await channel.send(f'>  [{status[camera_name]} warnings]')

    async def send_error(self, camera_name: str):
        """Send an error to all connected channels."""
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = f'Error: Camera feed "{camera_name}" is not responding.'
            text = f'@everyone plz fix!'
            embed = discord.Embed(title=title, description=text, color=0xff0000)
            await channel.send(embed=embed)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.content.startswith('!c2l-add'):
            channel_ids.append(message.channel.id)
            save_channel_ids()
            await message.channel.send(f'Roger that, {message.author.name}! I\'ll send warnings here.')

        if message.content.startswith('!c2l-remove'):
            channel_ids.remove(message.channel.id)
            save_channel_ids()
            await message.channel.send(f'No problem, {message.author.name}. I\'ll stop sending warnings here.')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        while True:
            await self.check_images()
            await asyncio.sleep(interval_min * 60)


client = Cam2LapseBot(intents=intents)
client.run(token)