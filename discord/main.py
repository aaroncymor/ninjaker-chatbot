import os
import logging.config, logging

import discord
from discord.ext import commands
from discord.errors import ClientException
import youtube_dl
import yaml

conf_env = os.getenv('CONFIG')
if not conf_env:
   raise Exception('CONFIG not set as an environment variable')

# load file
with open(conf_env) as f:
    config_data = yaml.load(f)

print(config_data)

# load logger
logging.config.dictConfig(config_data['logging'])
logger = logging.getLogger('NinjakerDiscordLogger')

# load configuration file
TOKEN = config_data['discord']['token']
COMMAND_PREFIX = config_data['discord']['command_prefix']
ALLOWED_TEXT_CHANNELS = config_data['discord']['allowed_text_channels']
ALLOWED_VOICE_CHANNELS = config_data['discord']['allowed_voice_channels']
ALLOWED_COMMANDS = config_data['discord']['allowed_commands']
MUSIC_TEXT_CHANNEL = config_data['discord']['music_text_channel']

client = commands.Bot(command_prefix=COMMAND_PREFIX)

@client.command()
async def ping(ctx):
    logger.debug("This is ctx", ctx.message)
    await ctx.send('pong')


@client.command()
async def join(ctx, target_channel : str):
    """Joins a voice channel"""

    text_channel = ctx.message.channel.name
    author_name = ctx.message.author.name

    logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tJoining a channel.".format(author_name, text_channel, target_channel))

    if text_channel != MUSIC_TEXT_CHANNEL:
        logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(author_name, MUSIC_TEXT_CHANNEL))
        await ctx.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
        return

    voice_channel = discord.utils.get(ctx.guild.voice_channels, name=target_channel)
    if ctx.voice_client is not None:
        logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tBot is connected to other channel. Moving bot to target channel."\
            .format(author_name, text_channel, target_channel))
        return await ctx.voice_client.move_to(voice_channel)
    
    # connect to target voice channel
    await voice_channel.connect()


@client.command()
async def play(ctx, url : str):
    """Play a youtube video"""

    try:
        text_channel = ctx.message.channel.name
        author_name = ctx.message.author.name

        logger.debug("Author:{0}\tText Channel:{1}\tPlaying a music.".format(author_name, text_channel))

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(author_name, MUSIC_TEXT_CHANNEL))
            await ctx.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return

        if ctx.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(author_name))
            return await ctx.send("Not connected to a voice channel. Please use `{0}join <voice_channel>` command.".format(COMMAND_PREFIX))

        # check for song.mp3 and remove
        song_there = os.path.isfile("song.mp3")
        try:
            logger.debug("Author:{0}\tText Channel:{1}\tAttempting to remove song.mp3 file".format(author_name, text_channel))
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            logger.debug("Author:{0}\tText Channel:{1}\tMusic is still playing.".format(author_name, text_channel))
            await ctx.send("Wait for the current music to end or use the `{0}stop` command.".format(COMMAND_PREFIX))
            return

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            logger.debug("Author:{0}\tText Channel:{1}\tError:Bot is not connected to a voice channel.".format(author_name, text_channel))
            await ctx.send("I am not present in any of the voice channels. Please use `{0}join <channel_name>` first.".format(COMMAND_PREFIX))
            return            
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        # download youtube video
        logger.debug("Author:{0}\tText Channel:{1}\tDownloading youtube link: {2}".format(author_name, text_channel, url))
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # rename file that ends with `.mp3` as song.mp3
        logger.debug("Author:{0}\tText Channel:{1}\tYoutube Link:{2}\tDownload complete. Renaming to song.mp3".format(author_name, text_channel, url))
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3")
        
        # attempt to play song.mp3
        logger.debug("Author:{0}\tText Channel:{1}\tAttempting to play song.mp3".format(author_name, text_channel))
        voice.play(discord.FFmpegPCMAudio("song.mp3"))
    except ClientException:
        logger.debug("Author:{0}\tText Channel:{1}\tError:Already connected to voice channel.".format(author_name, text_channel))
        await ctx.send("There is a song currently on play. Please use command `{cmd_prefix}stop` and then use command `{cmd_prefix}play <youtube_link>` again."\
            .format(cmd_prefix=COMMAND_PREFIX))
        return


@client.command()
async def stop(ctx):

    text_channel = ctx.message.channel.name
    author_name = ctx.message.author.name

    logger.debug("Author:{0}\tText Channel:{1}\tStop playing music and disconnect.".format(author_name, text_channel))

    if text_channel != MUSIC_TEXT_CHANNEL:
        logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(author_name, MUSIC_TEXT_CHANNEL))
        await ctx.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
        return

    if ctx.voice_client is None:
        logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(author_name))
        return await ctx.send("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()


@client.command()
async def pause(ctx):

    text_channel = ctx.message.channel.name
    author_name = ctx.message.author.name

    logger.debug("Author:{0}\tText Channel:{1}\tPause player.".format(author_name, text_channel))

    if text_channel != MUSIC_TEXT_CHANNEL:
        logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(author_name, MUSIC_TEXT_CHANNEL))
        await ctx.send("I am only allowed to play music in text channel 'play-music'.")
        return

    if ctx.voice_client is None:
        logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(author_name))
        return await ctx.send("Not connected to a voice channel. Please use `join <voice_channel>` command.")

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing.")


@client.command()
async def resume(ctx):

    text_channel = ctx.message.channel.name
    author_name = ctx.message.author.name

    logger.debug("Author:{0}\tText Channel:{1}\tResume paused player".format(author_name, text_channel))

    if text_channel != MUSIC_TEXT_CHANNEL:
        logger.debug("Author:{0}\tError:Text channel 'play-music' only allowed for this command".format(author_name, text_channel))
        await ctx.send("I am only allowed to play music in text channel 'play-music'.")
        return

    if ctx.voice_client is None:
        logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(author_name, text_channel))
        return await ctx.send("Not connected to a voice channel. Please use `join <voice_channel>` command.")

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio is not paused")


@client.command()
async def volume(ctx, volume: int):
    """Changes the player's volume"""

    text_channel = ctx.message.channel.name
    author_name = ctx.message.author.name

    logger.debug("Author:{0}\tText Channel:{1}\tChanging volume to {2}%.".format(author_name, text_channel, volume))

    if text_channel != MUSIC_TEXT_CHANNEL:
        logger.debug("Author:{0}\tError:Text channel 'play-music' only allowed for this command".format(author_name, text_channel))
        await ctx.send("I am only allowed to play music in text channel 'play-music'.")
        return

    if ctx.voice_client is None:
        logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(author_name, text_channel))
        return await ctx.send("Not connected to a voice channel. Please use `{0}join <voice_channel>` command.".format(COMMAND_PREFIX))

    ctx.voice_client.source.volume = volume / 100
    await ctx.send("Changed volume to {}%".format(volume))


client.run(TOKEN)

