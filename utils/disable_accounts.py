from disable_accounts_config import *
import sys

sys.path.append('..')

import discord, asyncio
from database import SMMWEDatabase

db = SMMWEDatabase()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}, disabling accounts ...')
    guild = client.get_guild(GUILD_ID)
    print(guild.name)
    for user in db.User.select():
        if len(user.user_id) > 10 and user.is_valid:  # Discord user
            if guild.get_member(int(user.user_id)) not in guild.get_role(VERIFIED_ROLE).members:
                print(f'Disable {user.username}\'s account')
                user.is_valid = False
                user.save()
    asyncio.get_event_loop().stop()

client.run(BOT_TOKEN)
