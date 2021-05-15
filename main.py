import os
import discord
import yaml

conf_env = os.getenv('CONFIG')
if not conf_env:
   raise Exception('CONFIG not set as an environment variable')

# load file
with open(conf_env) as f:
    config_data = yaml.load(f)

print(config_data)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(config_data['app']['discord_token'])

