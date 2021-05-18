import os
import logging.config, logging

import discord
from discord.errors import DiscordException, ClientException
import yaml
import youtube_dl

conf_env = os.getenv('CONFIG')
if not conf_env:
   raise Exception('CONFIG not set as an environment variable')

# load file
with open(conf_env) as f:
    config_data = yaml.load(f)

print(config_data)

TOKEN = config_data['discord']['token']
COMMAND_PREFIX = config_data['discord']['command_prefix']
ALLOWED_TEXT_CHANNELS = config_data['discord']['allowed_text_channels']
ALLOWED_VOICE_CHANNELS = config_data['discord']['allowed_voice_channels']
MUSIC_TEXT_CHANNEL = config_data['discord']['music_text_channel']
MUSIC_PLAYER_COMMANDS = config_data['discord']['music_player_commands']

# load logger
logging.config.dictConfig(config_data['logging'])
logger = logging.getLogger('NinjakerDiscordLogger')

client = discord.Client()

class MusicPlayer(object):

    def __init__(self, client, channel, guild, username, content, text_channel):

        if text_channel not in ALLOWED_TEXT_CHANNELS:
            raise PermissionError("The text_channel {} is not permitted for music player."\
            .format(text_channel))

        if text_channel != MUSIC_TEXT_CHANNEL:
            raise PermissionError("The text_channel {} is only allowed.".format(MUSIC_TEXT_CHANNEL))

        self.username = username
        self.content = content
        self.text_channel = text_channel
        self.channel = channel
        self.guild = guild
        self.voice = discord.utils.get(client.voice_clients, guild=guild)


    async def join(self):
        """Join a voice channel"""
        target_channel = self.content[len("{}join".format(COMMAND_PREFIX))+1:]

        voice_channel = discord.utils.get(self.guild.voice_channels, name=target_channel)
        if self.guild.voice_client is not None:
            logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tBot is connected to other channel. Moving bot to target channel {2}."\
                .format(self.username, self.text_channel, target_channel))
            return await self.guild.voice_client.move_to(voice_channel)

        if not voice_channel:
            raise ConnectionError("Voice channel {} does not exist!".format(target_channel))

        logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tConnecting to channel {2}.".format(self.username, self.text_channel, target_channel))
        await voice_channel.connect()
        return


    async def play(self):
        """Play given youtube link"""
        youtube_link = self.content[len("{}play".format(COMMAND_PREFIX))+1:]

        try:
            # check for song.mp3 and remove
            song_there = os.path.isfile("song.mp3")
            try:
                logger.debug("Author:{0}\tText Channel:{1}\tAttempting to remove song.mp3 file".format(self.username, self.text_channel))
                if song_there:
                    os.remove("song.mp3")
            except PermissionError:
                logger.debug("Author:{0}\tText Channel:{1}\tMusic is still playing.".format(self.username, self.text_channel))
                raise PermissionError("Wait for the current music to end or use the `{}stop` command.".format(COMMAND_PREFIX))

            if not self.voice.is_connected():
                logger.debug("Author:{0}\tText Channel:{1}\tError:Bot is not connected to a voice channel.".format(self.username, self.text_channel))
                raise ConnectionError("I am not present in any of the voice channels. Please use `{0}join <channel_name>` first.".format(COMMAND_PREFIX))

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }

            # download youtube video
            logger.debug("Author:{0}\tText Channel:{1}\tDownloading youtube link: {2}".format(self.username, self.text_channel, youtube_link))
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_link])
            
            # rename file that ends with `.mp3` as song.mp3
            logger.debug("Author:{0}\tText Channel:{1}\tYoutube Link:{2}\tDownload complete. Renaming to song.mp3".format(self.username, self.text_channel, youtube_link))
            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    os.rename(file, "song.mp3")
            
            # attempt to play song.mp3
            logger.debug("Author:{0}\tText Channel:{1}\tAttempting to play song.mp3".format(self.username, self.text_channel))
            self.voice.play(discord.FFmpegPCMAudio("song.mp3"))
        except discord.errors.ClientException:
            logger.debug("Author:{0}\tText Channel:{1}\tError:Already connected to voice channel.".format(self.username, self.text_channel))
            raise ClientException("There is a song currently on play. Please use command `{cmd_prefix}stop` and then use command `{cmd_prefix}play <youtube_link>` again."\
                .format(cmd_prefix=COMMAND_PREFIX))
        return


    async def resume(self):
        """If voice was paused. Resume playing."""
        logger.debug("Author:{0}\tText Channel:{1}\tResume paused player".format(self.username, self.text_channel))

        if self.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(self.username, self.text_channel))
            raise PermissionError("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))

        if not self.voice.is_paused():
            logger.debug("Author:{0}\tError:Player is not paused.".format(self.username, self.text_channel))
            raise DiscordException("The audio is not paused")

        self.voice.resume()
        return


    async def pause(self):
        """If voice is playing, pause it."""
        logger.debug("Author:{0}\tText Channel:{1}\tPause player.".format(self.username, self.text_channel))

        if self.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(self.username))
            raise ConnectionError("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))

        if not self.voice.is_playing():
            raise DiscordException("Currently no audio is playing.")

        self.voice.pause()
        return


    async def stop(self):
        """Leave the voice channel regardless if voice is playing or not."""

        logger.debug("Author:{0}\tText Channel:{1}\tStop playing music and disconnect.".format(self.username, self.text_channel))

        if self.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(self.username))
            raise ConnectionError("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
        
        if not self.voice.is_connected():
            raise ConnectionError("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
        
        await self.voice.disconnect()
        return


    async def volume(self):
        """Set the volume of voice client"""
        # slice string of command including space
        volume = self.content[len("{}volume".format(COMMAND_PREFIX))+1:]
        if not volume.isdigit():
            logger.debug("Author:{0}\tText Channel:{1}\tError: Volume cant be parsed.".format(self.username, self.text_channel))
            raise DiscordException("Volume cant be parsed.")

        logger.debug("Author:{0}\tText Channel:{1}\tChanging volume to {2}%.".format(self.username, self.text_channel, volume))

        if self.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(self.username, self.text_channel))
            raise ConnectionError("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
        
        self.guild.voice_client.source.volume = int(volume) / 100
        await self.channel.send("Changed volume to {}%".format(volume))
        return


    async def run_command(self, command):
        try:
            action = getattr(self, command) if hasattr(self, command) else None
            print("ACTION", action)
            if not action:
                await self.channel.send("Command not found in {}".format(self.__name__))
            await action()
        except Exception as e:
            logger.debug("Exception caught.\tError:{0}".format(e))
            await self.channel.send(e)


@client.event
async def on_ready():
    logger.debug('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    print(message)

    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    text_channel = str(message.channel.name)
    print(f'{username}: {user_message} ({text_channel})')

    # user is bot (client.user)
    if username == client.user:
        return

    if text_channel not in ALLOWED_TEXT_CHANNELS:
        print('{0} not in allowed channels.'.format(text_channel))
        return
    
    # Get command. The first element after content split by " "
    # Then substring removing prefix
    command = user_message.split(" ")[0][1:]
    if user_message.startswith(COMMAND_PREFIX):
        if command in MUSIC_PLAYER_COMMANDS:
            music_player = MusicPlayer(client, message.channel, message.guild, username, message.content, text_channel)
            await music_player.run_command(command)


client.run(TOKEN)

