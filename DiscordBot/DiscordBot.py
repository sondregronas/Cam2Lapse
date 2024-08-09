"""
Discord bot for monitoring the status of the Cam2Lapse cameras.

Code's a bit messy, will clean it up later. Not really ready for public use yet.

Required scopes:
- send messages
- slash commands
- mention everyone
"""
import os
import datetime
import discord
from pathlib import Path
from discord.ext import tasks
from dotenv import load_dotenv
import smtplib

load_dotenv()
# Load the Discord token from the environment
token = os.environ.get('DISCORD_TOKEN')

# How long to wait before sending a warning or error
warn_when = datetime.timedelta(minutes=30)
error_when = datetime.timedelta(hours=1)
# How long to wait between checking for new images
interval_min = 2

# Create the Discord client
intents = discord.Intents.default()


aliases = os.getenv('ALIASES', '').split(',')
aliases = [alias.split('=') for alias in aliases if alias]
aliases = {alias[0].strip(): alias[1].strip() for alias in aliases}
# Append .webp and add as duplicate entry
for alias in aliases.copy():
    aliases[f'{alias}.webp'] = f'{aliases[alias]}.webp'


def get_alias(camera_name: str) -> str:
    """Get the alias for a camera name."""
    return aliases.get(camera_name, camera_name)


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


SMTP_SERVER = os.getenv('SMTP_SERVER', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')
SMTP_TO = os.getenv('SMTP_TO', '').split(',')


channel_ids = load_channel_ids()
blacklist = load_blacklist()
status = {}
error_status = {}


class Cam2LapseBot(discord.Client):
    async def update_status(self) -> None:
        """Update the status of the bot."""
        statustext = f'{len(status)} feeds'
        if len(status) == 1:
            statustext = f'{len(status)} feed'
        if len(blacklist) > 0:
            statustext += f' ({len(blacklist)} ignored)'
        erroring_cameras = [camera for camera in error_status if error_status[camera].get('error', False)]
        if len(erroring_cameras) > 0:
            statustext += f' ({len(erroring_cameras)} down)'
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statustext))

    async def check_images(self):
        """Check the root directory for last modified date of .webp images."""
        for file in self.get_all_webp_in_img():
            file_name_no_ext = file.name.split('.webp')[0]
            if file.name not in status:
                status[file.name] = 0
                error_status[file_name_no_ext] = {}

            if file.name in blacklist:
                continue

            time_elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(file.stat().st_mtime)

            has_sent_warning = error_status[file_name_no_ext].get('warning', False)
            has_sent_error = error_status[file_name_no_ext].get('error', False)
            has_sent_warning_or_error = has_sent_warning or has_sent_error

            if time_elapsed > error_when:
                if not has_sent_error:
                    await self.send_error(file_name_no_ext)
            elif time_elapsed > warn_when:
                status[file.name] += 1
                if not has_sent_warning_or_error:
                    await self.send_warning(file_name_no_ext)
            else:
                if has_sent_error:
                    await self.send_okay(file_name_no_ext)
                error_status[file_name_no_ext] = {}
                status[file.name] = 0

        await self.update_status()

    def get_all_webp_in_img(self):
        if not any([file.is_file() for file in Path('img').iterdir()]):
            return self.get_all_webp_in_img_subfolders()
        return [file for file in Path('img').glob('*.webp')]

    @staticmethod
    def get_all_webp_in_img_subfolders():
        webp_files = []
        for folder in Path('img').iterdir():
            if folder.is_dir():
                for file in folder.glob('*.webp'):
                    webp_files.append(file)
        return webp_files

    async def get_status(self):
        """Returns a dictionary of camera names and their 'last modified' time."""
        last_seen = {}
        for file in self.get_all_webp_in_img():
            last_modified = datetime.datetime.fromtimestamp(file.stat().st_mtime)
            time_elapsed = datetime.datetime.now() - last_modified
            name = get_alias(file.name)
            if time_elapsed.seconds < 120:
                last_seen[name] = 'Pushed just now'
            elif time_elapsed.days > 1:
                last_seen[name] = f'Pushed {time_elapsed.days} days, {time_elapsed.seconds // 3600} hours ago'
            elif time_elapsed.seconds > 7200:
                last_seen[name] = f'Pushed {time_elapsed.seconds // 3600} hours ago'
            else:
                last_seen[name] = f'Pushed {time_elapsed.seconds // 60} minutes ago'
        return last_seen

    async def send_email(self, camera_name, online: bool):
        if not SMTP_SERVER:
            return
        try:
            smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            for email in SMTP_TO:
                if online:
                    message = f'Subject: Cam2Lapse: Camera "{camera_name}" is back online\n\n'
                else:
                    message = f'Subject: Cam2Lapse: Camera "{camera_name}" is not responding\n\nYou\'ll be notified when it\'s back online.'
                smtp.sendmail(SMTP_FROM, email, message)
            smtp.quit()
        except Exception:
            for channel_id in channel_ids:
                channel = self.get_channel(channel_id)
                title = 'Error with email notification'
                text = f'Failed to send out email notification for camera feed "{camera_name}"'
                embed = discord.Embed(title=title, description=text, color=0xffa000)
                embed.timestamp = datetime.datetime.now()
                await channel.send(embed=embed)

    async def send_warning(self, camera_name: str):
        """Send a warning to all connected channels."""
        error_status[camera_name]['warning'] = True
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = 'Warning'
            text = f'Camera feed \'{get_alias(camera_name)}\' has not sent an update in a while.'
            embed = discord.Embed(title=title, description=text, color=0xffa000)
            embed.timestamp = datetime.datetime.now()
            await channel.send(embed=embed)

    async def send_error(self, camera_name: str):
        """Send an error to all connected channels."""
        error_status[camera_name]['error'] = True
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = f'Error: Camera feed "{get_alias(camera_name)}" is not responding.'
            text = f'@everyone plz fix! (I will notify you when it\'s back online)'
            embed = discord.Embed(title=title, description=text, color=0xff0000)
            embed.timestamp = datetime.datetime.now()
            await channel.send(embed=embed)
            await self.send_email(get_alias(camera_name), False)

    async def send_okay(self, camera_name: str):
        """Send an okay message to all connected channels."""
        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            title = 'Camera restored'
            text = f'Camera feed "{get_alias(camera_name)}" is back online.'
            embed = discord.Embed(title=title, description=text, color=0x00ff00)
            embed.timestamp = datetime.datetime.now()
            await channel.send(embed=embed)
            await self.send_email(get_alias(camera_name), True)

    @tasks.loop(seconds=interval_min * 60)
    async def _loop(self):
        await self.check_images()


client = Cam2LapseBot(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} ({client.user.id})')
    await tree.sync()
    client._loop.start()


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
        embed.timestamp = datetime.datetime.now()
        await interaction.response.send_message(embed=embed)
    else:
        channel_ids.append(interaction.channel_id)
        embed = discord.Embed(title='Channel status', description=f'<#{interaction.channel_id}> added', color=0x00ff00)
        embed.timestamp = datetime.datetime.now()
        await interaction.response.send_message(embed=embed)
    save_channel_ids()


@tree.command(name='status')
async def _status(interaction):
    """Get the current status of all feeds"""
    last_seen = await client.get_status()
    embed = discord.Embed(title='Camera feed status', color=0x00ff00)
    for camera_name, last_seen_text in last_seen.items():
        if camera_name in blacklist:
            embed.add_field(name=f'~~{camera_name.split(".webp")[0]}~~', value=f'~~{last_seen_text}~~ **(blacklisted)**', inline=False)
            continue
        embed.add_field(name=camera_name.split('.webp')[0], value=last_seen_text, inline=False)
    if len(blacklist):
        embed.add_field(value='NOTE: *blacklisted cameras are not monitored*', name='')
    embed.add_field(value='Use `/toggle <feed>` to toggle monitoring for a feed', name='')
    embed.add_field(name='Subscribed channels', value=f'', inline=False)
    for channel in channel_ids:
        if interaction.guild.get_channel(channel):
            embed.add_field(name='', value=f'<#{channel}>', inline=False)
    embed.timestamp = datetime.datetime.now()
    await interaction.response.send_message(embed=embed)


@tree.command(name='toggle')
async def _toggle(interaction, camera_name: str):
    """Toggle monitoring on or off for the given camera"""
    camera_name = f'{camera_name}.webp'
    if camera_name in blacklist:
        blacklist.remove(camera_name)
        embed = discord.Embed(title='Camera feed status', color=0x00ff00)
        embed.add_field(name=camera_name, value='Monitoring', inline=False)
        embed.timestamp = datetime.datetime.now()
        await interaction.response.send_message(embed=embed)
    else:
        blacklist.append(camera_name)
        embed = discord.Embed(title='Camera feed status', color=0xffa000)
        embed.add_field(name=camera_name, value='Ignoring', inline=False)
        embed.timestamp = datetime.datetime.now()
        await interaction.response.send_message(embed=embed)
    save_blacklist()
    await client.update_status()

client.run(token)
