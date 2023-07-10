"""
Discord bot for monitoring the status of the Cam2Lapse cameras.

Code's a bit messy, will clean it up later. Not really ready for public use yet.

Required scopes:
- send messages
- slash commands
- mention everyone
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
                last_seen[file.name] = 'pushed just now'
            else:
                last_seen[file.name] = f'pushed {time_elapsed.seconds // 60} minutes ago'
        return last_seen

    async def send_warning(self, camera_name: str):
        """Send a warning to all connected channels."""
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = f'Warning: Camera feed "{camera_name}" has not sent an update in a while.'
            text = f'This is warning #{status[camera_name]}.'
            embed = discord.Embed(title=title, description=text, color=0xffa000)
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


client = Cam2LapseBot(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} ({client.user.id})')
    await tree.sync()
    while True:
        await client.check_images()
        await client.update_status()
        await asyncio.sleep(interval_min * 60)


@tree.command(name='ping')
async def _ping(interaction):
    """Replies with 'Pong!'"""
    await interaction.response.send_message('Pong!')


@tree.command(name='channel')
async def _channel(interaction):
    """Set or remove the current channel from error notifications"""
    if interaction.channel_id in channel_ids:
        channel_ids.remove(interaction.channel_id)
        embed = discord.Embed(title='Channel status', description=f'<#{interaction.channel_id}> removed', color=0xffa000)
        await interaction.response.send_message(embed=embed)
    else:
        channel_ids.append(interaction.channel_id)
        embed = discord.Embed(title='Channel status', description=f'<#{interaction.channel_id}> added', color=0x00ff00)
        await interaction.response.send_message(embed=embed)
    save_channel_ids()


@tree.command(name='status')
async def _status(interaction):
    """Get the current status of all feeds"""
    last_seen = await client.get_status()
    embed = discord.Embed(title='Camera feed status', color=0x00ff00)
    for camera_name, last_seen_text in last_seen.items():
        if camera_name.split('.webp')[0] in blacklist:
            embed.add_field(name=f'~~{camera_name.split(".webp")[0]}~~', value=f'~~{last_seen_text}~~ **(blacklisted)**', inline=False)
            continue
        embed.add_field(name=camera_name.split('.webp')[0], value=last_seen_text, inline=False)
    if len(blacklist):
        embed.add_field(value='NOTE: *blacklisted cameras are not monitored*', name='')
    embed.add_field(value='Use `/toggle <feed>` to toggle monitoring for a feed', name='')
    await interaction.response.send_message(embed=embed)


@tree.command(name='toggle')
async def _toggle(interaction, camera_name: str):
    """Toggle monitoring on or off for the given camera"""
    if camera_name in blacklist:
        blacklist.remove(camera_name)
        embed = discord.Embed(title='Camera feed status', color=0x00ff00)
        embed.add_field(name=camera_name, value='Monitoring', inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        blacklist.append(camera_name)
        embed = discord.Embed(title='Camera feed status', color=0xffa000)
        embed.add_field(name=camera_name, value='Ignoring', inline=False)
        await interaction.response.send_message(embed=embed)
    save_blacklist()
    await client.update_status()


client.run(token)
