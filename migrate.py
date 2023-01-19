#!/usr/bin/env python3
# Migrate from older versions of Engine Tribe
import database
from database import SMMWEDatabase
import asyncio

db = SMMWEDatabase()


async def migrate_from_old_to_new():
    for stats_item in await db.get_old_stats():
        print('- ' + stats_item.level_id)
        level = await db.get_level_from_level_id(stats_item.level_id)
        if level is not None:
            print('  Likes: ' + str(level.likes))
            for username in stats_item.likes_users.split(','):
                if username != '':
                    await db.add_like_user_only(level, username)
                    print('    - ' + username)
            print('  Dislikes: ' + str(level.dislikes))
            for username in stats_item.dislikes_users.split(','):
                if username != '':
                    await db.add_dislike_user_only(level, username)
                    print('    - ' + username)


async def dump_level_data_database():
    import json
    results: list[dict] = []
    for from_id, limit in [(1, 500), (501, 500), (1001, 500), (1501, 500), (2001, 500), (2501, 500), (3001, 149)]:
        print(from_id, limit)
        for level in await db.get_all_level_datas_in(from_id, limit):
            db_id = level.id
            level_id = level.level_id
            level_data = level.level_data.decode()
            level_checksum = level.level_checksum
            results.append({
                'id': db_id,
                'level_id': level_id,
                'level_data': level_data,
                'level_checksum': level_checksum
            })
    with open('level_data.json', 'w') as f:
        f.write(json.dumps(results, indent=4))


async def import_single_level(level_data: dict):
    await db.add_level_data(
        level_id=level_data['level_id'],
        level_data=level_data['level_data'],
        level_checksum=level_data['level_checksum']
    )
    print(f"imported level with id: {level_data['level_id']}")


async def import_level_data_database():
    import json
    level_datas = json.loads(open('/home/yidaozhan/level_data_without_duplicate.json', 'r').read())
    for level_data in level_datas:
        asyncio.create_task(import_single_level(level_data))
        await asyncio.sleep(0.5)
    await asyncio.sleep(1000000000000000)


def remove_duplicates():
    import csv, json
    level_infos = csv.reader(open('level_table without duplicate.csv', 'r'))
    level_ids = [row[13] for row in level_infos]
    level_datas = json.loads(open('level_data.json', 'r').read())

    for level_data in level_datas:
        if level_data['level_id'] not in level_ids:
            print(f"remove level with id: {level_data['level_id']}")
            level_datas.remove(level_data)

    with open('level_data_without_duplicate.json', 'w') as f:
        f.write(json.dumps(level_datas))


asyncio.run(import_level_data_database())
