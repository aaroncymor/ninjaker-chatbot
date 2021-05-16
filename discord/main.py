import os
import discord
import logging.config, logging

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

# load logger
logging.config.dictConfig(config_data['logging'])
logger = logging.getLogger('NinjakerDiscordLogger')

client = discord.Client()

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

    # join command
    if message.content.startswith("{}join".format(COMMAND_PREFIX)):
 
        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(username, MUSIC_TEXT_CHANNEL))
            await message.channel.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return            

        # slice string of command including space
        target_channel = user_message[len("{}join".format(COMMAND_PREFIX))+1:]
        
        logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tJoining a channel.".format(username, text_channel, target_channel))

        voice_channel = discord.utils.get(message.guild.voice_channels, name=target_channel)
        if message.guild.voice_client is not None:
            logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tBot is connected to other channel. Moving bot to target channel {2}."\
                .format(username, text_channel, target_channel))
            return await message.guild.voice_client.move_to(voice_channel)            

        logger.debug("Author:{0}\tText Channel:{1}\tTarget Voice Channel:{2}\tConnecting to channel {2}.".format(username, text_channel, target_channel))
        await voice_channel.connect()
        return
    
    # play command
    if message.content.startswith("{}play".format(COMMAND_PREFIX)):

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(username, MUSIC_TEXT_CHANNEL))
            await message.channel.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return
        
        if message.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(username))
            await message.channel.send("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
            return

        try:
            # slice string of command including space
            youtube_link = user_message[len("{}play".format(COMMAND_PREFIX))+1:]

            # check for song.mp3 and remove
            song_there = os.path.isfile("song.mp3")
            try:
                logger.debug("Author:{0}\tText Channel:{1}\tAttempting to remove song.mp3 file".format(username, text_channel))
                if song_there:
                    os.remove("song.mp3")
            except PermissionError:
                logger.debug("Author:{0}\tText Channel:{1}\tMusic is still playing.".format(username, text_channel))
                await message.channel.send("Wait for the current music to end or use the `{}stop` command.".format(COMMAND_PREFIX))
                return

            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if not voice.is_connected():
                logger.debug("Author:{0}\tText Channel:{1}\tError:Bot is not connected to a voice channel.".format(username, text_channel))
                await message.channel.send("I am not present in any of the voice channels. Please use `{0}join <channel_name>` first.".format(COMMAND_PREFIX))
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
            logger.debug("Author:{0}\tText Channel:{1}\tDownloading youtube link: {2}".format(username, text_channel, youtube_link))
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_link])
            
            # rename file that ends with `.mp3` as song.mp3
            logger.debug("Author:{0}\tText Channel:{1}\tYoutube Link:{2}\tDownload complete. Renaming to song.mp3".format(username, text_channel, youtube_link))
            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    os.rename(file, "song.mp3")
            
            # attempt to play song.mp3
            logger.debug("Author:{0}\tText Channel:{1}\tAttempting to play song.mp3".format(username, text_channel))
            voice.play(discord.FFmpegPCMAudio("song.mp3"))
        except discord.errors.ClientException:
            logger.debug("Author:{0}\tText Channel:{1}\tError:Already connected to voice channel.".format(username, text_channel))
            await message.channel.send("There is a song currently on play. Please use command `{cmd_prefix}stop` and then use command `{cmd_prefix}play <youtube_link>` again."\
                .format(cmd_prefix=COMMAND_PREFIX))
            return            

    # pause command
    if message.content.startswith("{}pause".format(COMMAND_PREFIX)):
        logger.debug("Author:{0}\tText Channel:{1}\tPause player.".format(username, text_channel))

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(username, MUSIC_TEXT_CHANNEL))
            await message.channel.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return

        if message.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(username))
            await message.channel.send("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
            return

        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await message.channel.send("Currently no audio is playing.")
            return

    # resume command
    if message.content.startswith("{}resume".format(COMMAND_PREFIX)):
        logger.debug("Author:{0}\tText Channel:{1}\tResume paused player".format(username, text_channel))

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel 'play-music' only allowed for this command".format(username, text_channel))
            await message.channel.send("I am only allowed to play music in text channel 'play-music'.")
            return

        if message.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(username, text_channel))
            await message.channel.send("Not connected to a voice channel. Please use `join <voice_channel>` command.")
            return

        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice.is_paused():
            voice.resume()
        else:
            await message.channel.send("The audio is not paused")
            return

    # stop command
    if message.content.startswith("{}stop".format(COMMAND_PREFIX)):
        logger.debug("Author:{0}\tText Channel:{1}\tStop playing music and disconnect.".format(username, text_channel))

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel '{1}' only allowed for this command".format(username, MUSIC_TEXT_CHANNEL))
            await message.channel.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return

        if message.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(username))
            await message.channel.send("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
            return
        
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice.is_connected():
            await voice.disconnect()
            return

    #volume command
    if message.content.startswith("{}volume".format(COMMAND_PREFIX)):

        # slice string of command including space
        try:
            volume = int(user_message[len("{}volume".format(COMMAND_PREFIX))+1:])
        except ValueError:
            logger.debug("Author:{0}\tText Channel:{1}\tError: Volume cant be parsed.".format(username, text_channel))

        logger.debug("Author:{0}\tText Channel:{1}\tChanging volume to {2}%.".format(username, text_channel, volume))

        if text_channel != MUSIC_TEXT_CHANNEL:
            logger.debug("Author:{0}\tError:Text channel 'play-music' only allowed for this command".format(username, text_channel))
            await message.channel.send("I am only allowed to play music in text channel '{}'.".format(MUSIC_TEXT_CHANNEL))
            return

        if message.guild.voice_client is None:
            logger.debug("Author:{0}\tError:Not connected to a voice channel.".format(username, text_channel))
            await message.channel.send("Not connected to a voice channel. Please use `{}join <voice_channel>` command.".format(COMMAND_PREFIX))
            return
        
        message.guild.voice_client.source.volume = volume / 100
        await message.channel.send("Changed volume to {}%".format(volume))
        return

client.run(TOKEN)

