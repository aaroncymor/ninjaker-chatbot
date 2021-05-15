import os
import logging.config, logging

import discord
from discord.ext import commands
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

client = commands.Bot(command_prefix=COMMAND_PREFIX)

@client.command()
async def ping(ctx):
    logger.debug("This is ctx", ctx)
    await ctx.send('pong')


@client.command()
async def play(ctx, url : str):
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Wait for the current music to end or use the `stop` command")
        return

    voice_channel = discord.utils.get(ctx.guild.voice_channels, name='DOTAmbayan Voice Chat')
    await voice_channel.connect()
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")
    
    voice.play(discord.FFmpegPCMAudio("song.mp3"))

@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing.")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio is not paused")


@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()

client.run(TOKEN)

