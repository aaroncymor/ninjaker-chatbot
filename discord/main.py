import os
import logging.config, logging

import discord
from discord.ext import commands
from datetime import datetime
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
ALLOWED_CHANNELS = config_data['discord']['allowed_channels']
ALLOWED_COMMANDS = config_data['discord']['allowed_commands']

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

@bot.command()
async def ping(ctx):
    logger.debug("this is a test - pong")
    await ctx.send('pong')

bot.run(TOKEN)

# client = discord.Client()

# @client.event
# async def on_ready():
#     logger.debug('We have logged in as {0.user}'.format(client))

# @client.event
# async def on_message(message):
#     username = str(message.author).split('#')[0]
#     user_message = str(message.content)
#     channel = str(message.channel.name)
#     print(f'{username}: {user_message} ({channel})')

#     if username == client.user:
#         return

#     if channel not in ALLOWED_CHANNELS:
#         print('{0} not in allowed channels.'.format(channel))
#         return

#     if message.content.startswith('!hello'):
#         await message.channel.send('Hello!')

# client.run(config_data['discord']['token'])

