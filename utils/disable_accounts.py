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
    print(len(guild.get_role(VERIFIED_ROLE).members))
    for user in db.User.select():
        if len(user.user_id) > 10:  # Discord user
            #print(guild.get_member(int(user.user_id)) not in guild.get_role(VERIFIED_ROLE).members)
            member = guild.get_member(int(user.user_id))
            if member:
                if member not in guild.get_role(VERIFIED_ROLE).members:
                    print(f'Disable {user.username} ({member.name})\'s account')
                    user.is_valid = False
                    #user.save()
                else:
                    user.is_valid = True
                    #user.save()
    asyncio.get_event_loop().stop()

client.run(BOT_TOKEN)
