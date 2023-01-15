#!/usr/bin/env python3
# Migrate from older versions of Engine Tribe
import database
from database import SMMWEDatabase
import asyncio

db = SMMWEDatabase()


async def main():
    for stats_item in await db.get_old_stats():
        print('- ' + stats_item.level_id)
        level = await db.get_level_from_level_id(stats_item.level_id)
        print('  Likes: ' + str(level.likes))
        for username in stats_item.likes_users.split(','):
            await db.add_like_user_only(level, username)
            print('    - '+username)
        print('  Dislikes: ' + str(level.dislikes))
        for username in stats_item.dislikes_users.split(','):
            await db.add_dislike_user_only(level, username)
            print('    - '+username)


asyncio.run(main())
