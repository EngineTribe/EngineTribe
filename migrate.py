#!/usr/bin/env python3
# Migrate from older versions of Engine Tribe
# SOME CODES WILL NOT WORK AS EXPECTED
import database
from database.db import Database
from database.db_access import DBAccessLayer
from database.db_migration import DBMigrationAccessLayer
import asyncio

db = Database()


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


###

async def old_users_to_new_users():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_user in await dal_migrate.get_all_old_users():
                print(f"trying to import user with name: {old_user.username}")
                await dal_migrate.add_user(
                    username=old_user.username,
                    password_hash=old_user.password_hash,
                    im_id=int(old_user.user_id),
                    uploads=old_user.uploads,
                    is_admin=old_user.is_admin,
                    is_mod=old_user.is_mod,
                    is_banned=old_user.is_banned,
                    is_valid=old_user.is_valid,
                    is_booster=old_user.is_booster
                )
                print(f"imported user with id: {old_user.user_id}")
            await dal.commit()


async def old_levels_to_new_levels():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_level in await dal_migrate.get_all_old_levels():
                print(f"trying to import level with id: {old_level.level_id}")
                author = await dal.get_user_by_username(old_level.author)
                if author is None:
                    print(f"author {old_level.author} not found")
                    author_id = 0
                else:
                    author_id = author.id
                record_user = await dal.get_user_by_username(old_level.record_user)
                if record_user is None:
                    print(f"record user {old_level.record_user} not found")
                    record_user_id = 0
                else:
                    record_user_id = record_user.id
                await dal_migrate.add_level(
                    level_id=old_level.level_id,
                    name=old_level.name,
                    style=old_level.style,
                    environment=old_level.environment,
                    tag_1=old_level.tag_1,
                    tag_2=old_level.tag_2,
                    non_latin=old_level.non_latin,
                    testing_client=old_level.testing_client,
                    record=old_level.record,
                    author_id=author_id,
                    record_user_id=record_user_id,
                    likes=old_level.likes,
                    dislikes=old_level.dislikes,
                    clears=old_level.clears,
                    deaths=old_level.deaths,
                    plays=old_level.plays,
                    featured=old_level.featured
                )
                print(f"imported level with id: {old_level.level_id}")
            await dal.commit()


async def old_level_data_to_new_level_data():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_level_data in await dal_migrate.get_all_old_level_datas():
                print(f"trying to import level data with id: {old_level_data.level_id}")
                if isinstance(old_level_data.level_data, str):
                    level_data = old_level_data.level_data.encode()
                else:
                    level_data = old_level_data.level_data
                if dal.get_level_by_level_id(old_level_data.level_id) is not None:
                    await dal.add_level_data(
                        level_id=old_level_data.level_id,
                        level_data=level_data,
                        level_checksum=old_level_data.level_checksum
                    )
                    print(f"imported level data with id: {old_level_data.level_id}")
            await dal.commit()


async def old_likes_to_new_likes():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_like in await dal_migrate.get_all_old_likes():
                print(f"trying to import like with id: {old_like.id} {old_like.parent_id}")
                old_level = await dal_migrate.get_old_level_from_parent_id(old_like.parent_id)
                if old_level is None:
                    print(f"level with parent id {old_like.parent_id} not found")
                    continue
                new_level = await dal.get_level_by_level_id(old_level.level_id)
                print(f"old level id: {old_like.parent_id} -> new level id: {new_level.id}")
                user = await dal.get_user_by_username(old_like.username)
                if user is None:
                    print(f"user with username {old_like.username} not found")
                    continue
                await dal_migrate.add_like_user_only(
                    user_id=user.id,
                    parent_id=new_level.id
                )
            await session.commit()


async def old_dislikes_to_new_dislikes():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_dislike in await dal_migrate.get_all_old_dislikes():
                print(f"trying to import dislike with id: {old_dislike.id} {old_dislike.parent_id}")
                old_level = await dal_migrate.get_old_level_from_parent_id(old_dislike.parent_id)
                if old_level is None:
                    print(f"level with parent id {old_dislike.parent_id} not found")
                    continue
                new_level = await dal.get_level_by_level_id(old_level.level_id)
                print(f"old level id: {old_dislike.parent_id} -> new level id: {new_level.id}")
                user = await dal.get_user_by_username(old_dislike.username)
                if user is None:
                    print(f"user with username {old_dislike.username} not found")
                    continue
                await dal_migrate.add_dislike_user_only(
                    user_id=user.id,
                    parent_id=new_level.id
                )
            await session.commit()


async def old_clears_to_new_clears():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for old_clear in await dal_migrate.get_all_old_clears():
                print(f"trying to import clear with id: {old_clear.id} {old_clear.parent_id}")
                old_level = await dal_migrate.get_old_level_from_parent_id(old_clear.parent_id)
                if old_level is None:
                    print(f"level with parent id {old_clear.parent_id} not found")
                    continue
                new_level = await dal.get_level_by_level_id(old_level.level_id)
                print(f"old level id: {old_clear.parent_id} -> new level id: {new_level.id}")
                user = await dal.get_user_by_username(old_clear.username)
                if user is None:
                    print(f"user with username {old_clear.username} not found")
                    continue
                await dal_migrate.add_clear_user_only(
                    user_id=user.id,
                    parent_id=new_level.id
                )


async def remove_duplicate_levels():
    levels: dict[str, int] = {}  # level name -> author id
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for level in await dal_migrate.get_all_levels():
                if level.name in levels and levels[level.name] == level.author_id:
                    print(f"found duplicate level: {level.name}, deleting")
                    await dal_migrate.delete_level(level.id)
                    try:
                        await dal_migrate.delete_level_data(level.level_id)
                    except Exception as e:
                        print(f"could not delete corresponding level data: {e}")
                    try:
                        await dal_migrate.delete_stats(level.id)
                    except Exception as e:
                        print(f"could not delete corresponding stats: {e}")
                else:
                    levels[level.name] = level.author_id


async def sync_featured_from_old_level():
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            dal_migrate = DBMigrationAccessLayer(session)
            for level in await dal_migrate.get_all_old_featured_levels():
                print(f"trying to sync featured level with id: {level.id}")
                new_level = await dal.get_level_by_level_id(level.level_id)
                if new_level is None:
                    print(f"level with id {level.level_id} not found")
                    continue
                await dal.set_featured(level=new_level, is_featured=True)
            await session.commit()


asyncio.run(sync_featured_from_old_level())
