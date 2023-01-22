from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Level, LevelData, User, ClearedUsers, LikeUsers, DislikeUsers, Stats
import datetime
from sqlalchemy import func, select, delete


class DBAccessLayer:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_level(self, name: str, style: int, environment: int, tag_1: int, tag_2: int, author: str,
                        level_id: str, non_latin: bool, testing_client: bool, description: str):
        # add level metadata into database
        level = Level(name=name, likes=0, dislikes=0, plays=0, deaths=0, clears=0,
                      style=style, environment=environment, tag_1=tag_1, tag_2=tag_2,
                      date=datetime.date.today(), author=author,
                      level_id=level_id, non_latin=non_latin, record_user='', record=0,
                      testing_client=testing_client, description=description, featured=False)
        self.session.add(level)
        await self.session.flush()

    async def update_user(self, user: User):
        self.session.add(user)
        await self.session.flush()

    async def add_user(self, username: str, password_hash: str, user_id: str):
        # register user
        user = User(username=username, password_hash=password_hash, user_id=user_id, uploads=0, is_admin=False,
                    is_mod=False, is_booster=False, is_valid=True, is_banned=False)

        self.session.add(user)
        await self.session.flush()

    async def execute_selection(self, selection) -> list:
        return (await self.session.execute(
            selection
        )).scalars().all()

    async def get_like_type(self, level: Level, username: str) -> str:
        # get user's like type (like or dislike or none) of a level
        like = (await self.session.execute(
            select(LikeUsers).where(LikeUsers.parent_id == level.id,
                                    LikeUsers.username == username)
        )).scalars().first()
        dislike = (await self.session.execute(
            select(DislikeUsers).where(DislikeUsers.parent_id == level.id,
                                       DislikeUsers.username == username)
        )).scalars().first()
        if like is not None:
            return '0'  # like
        elif dislike is not None:
            return '1'  # dislike
        else:
            return '3'  # none

    async def add_like_to_level(self, username: str, level: Level):
        # add like to level
        like = LikeUsers(parent_id=level.id, username=username)
        level.likes += 1
        self.session.add_all([like, level])
        await self.session.flush()

    async def add_dislike_to_level(self, username: str, level: Level):
        # add dislike to level
        dislike = DislikeUsers(parent_id=level.id, username=username)
        level.dislikes += 1
        self.session.add_all([dislike, level])
        await self.session.flush()

    async def add_play_to_level(self, level: Level):
        # add play to level
        level.plays += 1
        self.session.add(level)
        await self.session.flush()

    async def add_death_to_level(self, level: Level):
        # add death to level
        level.deaths += 1
        self.session.add(level)
        await self.session.flush()

    async def add_clear_to_level(self, username: str, level: Level):
        # add clear to level
        if (await self.session.execute(
                select(ClearedUsers).where(ClearedUsers.parent_id == level.id,
                                           ClearedUsers.username == username)
        )).scalars().first() is None:
            clear = ClearedUsers(parent_id=level.id, username=username)
            self.session.add(clear)
        level.clears += 1
        self.session.add(level)
        await self.session.flush()

    async def update_record_to_level(self, username: str, level: Level, record: int):
        # update record to level
        level.record_user = username
        level.record = record
        self.session.add(level)
        await self.session.flush()

    async def get_user_from_username(self, username: str) -> User | None:
        # get user from username
        user = (await self.session.execute(
            select(User).where(User.username == username)
        )).scalars().first()
        return user if (user is not None) else None

    async def get_user_from_user_id(self, user_id: str) -> User | None:
        # get user from user id
        user = (await self.session.execute(
            select(User).where(User.user_id == user_id)
        )).scalars().first()
        return user if (user is not None) else None

    async def get_level_from_level_id(self, level_id: str) -> Level | None:
        # get level from level id
        level = (await self.session.execute(
            select(Level).where(Level.level_id == level_id)
        )).scalars().first()
        return level if (level is not None) else None

    async def get_clear_type(self, level: Level, username: str) -> str:
        # get user's clear type (yes or no) of a level
        clear = (await self.session.execute(
            select(ClearedUsers).where(ClearedUsers.parent_id == level.id,
                                       ClearedUsers.username == username)
        )).scalars().first()
        if clear is not None:
            return 'yes'
        else:
            return 'no'

    async def get_liked_levels_by_user(self, username: str) -> list[LikeUsers]:
        # get user's liked levels
        return (
            await self.session.execute(
                select(LikeUsers).where(LikeUsers.username == username)
            )
        ).scalars().all()

    async def get_disliked_levels_by_user(self, username: str) -> list[DislikeUsers]:
        # get user's disliked levels
        return (
            await self.session.execute(
                select(DislikeUsers).where(DislikeUsers.username == username)
            )
        ).scalars().all()

    async def get_cleared_levels_by_user(self, username: str) -> list[ClearedUsers]:
        # get user's cleared levels
        return (
            await self.session.execute(
                select(ClearedUsers).where(ClearedUsers.username == username)
            )
        ).scalars().all()

    async def add_level_data(self, level_id: str, level_data, level_checksum: str):
        # add level data into database as bytes
        if isinstance(level_data, str):
            level_data = level_data.encode()
            level_data_item = LevelData(
                level_id=level_id,
                level_data=level_data,
                level_checksum=level_checksum
            )
            self.session.add(level_data_item)
            await self.session.flush()

    async def dump_level_data(self, level_id: str) -> LevelData | None:
        level_data_item = (await self.session.execute(
            select(LevelData).where(LevelData.level_id == level_id)
        )).scalars().first()
        if level_data_item is not None:
            return level_data_item
        else:
            return None

    async def delete_level(self, level: Level):
        await self.session.delete(level)
        await self.session.execute(
            delete(LikeUsers).where(LikeUsers.parent_id == level.id)
        )
        await self.session.execute(
            delete(DislikeUsers).where(LikeUsers.parent_id == level.id)
        )
        await self.session.flush()

    async def delete_level_data(self, level_id: str):
        level_data_item = (await self.session.execute(
            LevelData.where(LevelData.level_id == level_id)
        )).scalars().first()
        level_data_item.delete()
        self.session.add(level_data_item)
        await self.session.flush()

    async def set_featured(self, level: Level, is_featured: bool):
        level.featured = is_featured
        self.session.add(level)
        await self.session.flush()

    async def get_level_count(self, selection=None) -> int:
        if selection is None:
            selection = select(Level)
        return (
            await self.session.execute(
                select(func.count()).select_from(selection)
            )
        ).scalars().first()

    async def get_player_count(self) -> int:
        return (
            await self.session.execute(
                select(func.count()).select_from(User)
            )
        ).scalars().first()

    async def commit(self):
        await self.session.commit()

    # Code below are for migration

    async def get_old_stats(self) -> list[Stats]:
        return (
            await self.session.execute(
                select(Stats)
            )
        ).scalars().all()

    async def add_like_user_only(self, level: Level, username: str):
        like = LikeUsers(parent_id=level.id, username=username)
        self.session.add(like)
        await self.session.commit()

    async def add_dislike_user_only(self, level: Level, username: str):
        dislike = DislikeUsers(parent_id=level.id, username=username)
        self.session.add(dislike)
        await self.session.commit()

    async def get_all_level_datas_in(self, range_from, limit) -> list[LevelData]:
        # use offset
        return (await self.session.execute(
            select(LevelData).offset(range_from).limit(limit)
        )).scalars().all()
