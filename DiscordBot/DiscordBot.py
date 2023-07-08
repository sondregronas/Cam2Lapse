"""
Discord bot for monitoring the status of the Cam2Lapse cameras.

Temporary solution until I can get a proper monitoring system set up.

Code's a bit messy, will clean it up later.

Could add livefeeds and metadata later, but just wanted to get a notification when a camera goes down for now.
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
interval_min = 60

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


def load_blacklist() -> list:
    """Load the blacklist from the file."""
    if not os.path.exists('blacklist.txt'):
        return []

    with open('blacklist.txt', 'r') as f:
        return [feed for feed in f.read().split('\n') if feed]


def save_blacklist() -> None:
    """Save the blacklist to the file."""
    with open('blacklist.txt', 'w+') as f:
        converted = [str(feed) for feed in blacklist]
        f.write('\n'.join(converted) + '\n')


channel_ids = load_channel_ids()
blacklist = load_blacklist()
status = {}


class Cam2LapseBot(discord.Client):
    async def update_status(self) -> None:
        """Update the status of the bot."""
        statustext = f'{len(status)} feeds'
        if len(status) == 1:
            statustext = f'{len(status)} feed'
        if len(blacklist) > 0:
            statustext += f' ({len(blacklist)} ignored)'
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statustext))

    async def check_images(self):
        """Check the root directory for last modified date of .webp images."""
        for file in Path('img').glob('*.webp'):
            if file.name in blacklist:
                if file.name in status:
                    del status[file.name]
                continue

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

        await self.update_status()


    async def get_status(self):
        """Returns a dictionary of camera names and their 'last modified' time."""
        last_seen = {}
        for file in Path('img').glob('*.webp'):
            if file.name in blacklist:
                continue
            time_elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(file.stat().st_mtime)
            if time_elapsed.seconds < 120:
                last_seen[file.name] = 'just now'
            else:
                last_seen[file.name] = f'{time_elapsed.seconds // 60} minutes ago'
        return last_seen


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

        match message.content.split():
            case ['!c2l-add']:
                if message.channel.id in channel_ids:
                    await message.channel.send(f'I\'m already sending warnings here, {message.author.mention}!')
                    return
                channel_ids.append(message.channel.id)
                save_channel_ids()
                await message.channel.send(f'Roger that, {message.author.mention}! I\'ll send warnings in {message.channel.mention}.')

            case ['!c2l-remove']:
                if message.channel.id not in channel_ids:
                    await message.channel.send(f'I wasn\'t sending warnings in {message.channel.mention} to begin with, {message.author.mention}!')
                    return
                channel_ids.remove(message.channel.id)
                save_channel_ids()
                await message.channel.send(f'No problem, {message.author.mention}. I\'ll stop sending warnings in {message.channel.mention}.')

            case ['!c2l-list']:
                last_seen = await self.get_status()

                if len(status) == 0:
                    text = '**I\'m not watching any feeds right now.**\n'
                else:
                    text = 'Here are the feeds I\'m watching:\n'
                    for feed in status:
                        text += f'* {feed.split(".webp")[0]} - _({last_seen[feed]})_\n'

                if len(blacklist) == 0:
                    text += '\n**I\'m not ignoring any feeds right now.**\n'
                else:
                    text += '\nAnd here are the feeds I\'m ignoring:\n '
                    for feed in blacklist:
                        text += f'* {feed.split(".webp")[0]}\n'

                text += '\n_Use `!c2l-toggle <camera>` to toggle a camera feed._'

                await message.channel.send(text)

            case ['!c2l-toggle', feed]:
                if not feed.endswith('.webp'):
                    feed = feed + '.webp'
                if feed not in status and feed not in blacklist:
                    await message.channel.send(f'Sorry, but I don\'t recognize that feed, {message.author.mention}!')
                    return
                if feed in blacklist:
                    blacklist.remove(feed)
                    status[feed] = 0
                    save_blacklist()
                    await message.channel.send(f'Roger that, {message.author.mention}! I\'ll monitor the feed.')
                else:
                    blacklist.append(feed)
                    if feed in status:
                        status.pop(feed)
                    save_blacklist()
                    await message.channel.send(f'No problem, {message.author.mention}. I\'ll stop monitoring the feed.')
                await self.update_status()

            case ['!c2l' | '!c2l-help' | '!c2l-commands']:
                await message.channel.send(f'Here are the commands I respond to:\n'
                                           f'`!c2l-add` - Add this channel to the list of channels to send warnings to.\n'
                                           f'`!c2l-remove` - Remove this channel from the list of channels to send warnings to.\n'
                                           f'`!c2l-list` - List all camera feeds I\'m watching or ignoring.\n'
                                           f'`!c2l-toggle <camera feed>` - Toggle warnings for a specific camera feed.\n'
                                           f'`!c2l` | `!c2l-help` | `!c2l-commands` - Show this message.')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        while True:
            await self.check_images()
            await asyncio.sleep(interval_min * 60)


client = Cam2LapseBot(intents=intents)
client.run(token)
