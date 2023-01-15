from config import *
import datetime
from sqlalchemy import Column, Integer, UnicodeText, Text, Date, Boolean, LargeBinary
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import ssl

Base = declarative_base()


class SMMWEDatabase:
    def __init__(self):
        match DATABASE_ADAPTER:
            case 'mysql':
                database_type = 'mysql+asyncmy'
            case 'postgresql':
                database_type = 'postgresql+asyncpg'
            case 'sqlite':
                database_type = 'sqlite+aiosqlite'
            case _:
                raise ValueError('Invalid database adapter')
        url: str = f'{database_type}://{DATABASE_USER}:{DATABASE_PASS}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
        if DATABASE_SSL:
            ssl_ctx = ssl.create_default_context(cafile="/etc/ssl/certs/ca-certificates.crt")
            ssl_ctx.verify_mode = ssl.CERT_REQUIRED
            connect_args = {
                'ssl': ssl_ctx
            }
        else:
            connect_args = {}
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=DATABASE_DEBUG, future=True,
            connect_args=connect_args
        )
        # Base.metadata.create_all(self.engine)
        self.session: sessionmaker = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    class Level(Base):
        __table_args = {'mysql_charset': 'utf8mb4'}
        __mapper_args__ = {"eager_defaults": True}
        __tablename__ = "level_table"

        id = Column(Integer, primary_key=True)

        name = Column(UnicodeText)  # Level name
        likes = Column(Integer)  # Likes count
        dislikes = Column(Integer)  # Dislikes count
        plays = Column(Integer)  # Play count
        deaths = Column(Integer)  # Death count
        clears = Column(Integer)  # Clear count
        style = Column(Integer)  # Game style
        environment = Column(Integer)  # Level environment
        tag_1 = Column(Integer)  # Tag 1
        tag_2 = Column(Integer)  # Tag 2
        date = Column(Date)  # Upload date
        author = Column(Text)  # Level maker
        level_id = Column(Text)  # Level ID
        non_latin = Column(Boolean)  # Whether the level name contains non-Latin characters
        featured = Column(Boolean)  # Whether the level is in promising levels
        record_user = Column(Text)  # Record user
        record = Column(Integer)  # Record
        testing_client = Column(Boolean)  # For 3.3.0+ testing client
        description = Column(UnicodeText)  # Level description
        # archivo = Column(Text)  # Level file in storage backend   # deprecated
        # comments = Column(Integer)  # Unimplemented in original server

    class LikeUsers(Base):
        __tablename__ = "likes_table"

        id = Column(Integer, primary_key=True)
        parent_id = Column(Integer)

        username = Column(Text)

    class DislikeUsers(Base):
        __tablename__ = "dislikes_table"

        id = Column(Integer, primary_key=True)
        parent_id = Column(Integer)

        username = Column(Text)

    class ClearedUsers(Base):
        __tablename__ = "clears_table"

        id = Column(Integer, primary_key=True)
        parent_id = Column(Integer)

        username = Column(Text)

    class User(Base):
        __tablename__ = "user_table"

        id = Column(Integer, primary_key=True)

        username = Column(Text)  # User name
        user_id = Column(Text)  # Engine Bot is run across IMs, so user id is string
        uploads = Column(Integer)  # Upload levels count
        password_hash = Column(Text)  # Password hash
        is_admin = Column(Boolean)  # Is administrator
        is_mod = Column(Boolean)  # Is moderator
        is_booster = Column(Boolean)  # Is booster
        is_valid = Column(Boolean)  # Is account valid (Engine-bot determines whether account is still in the QQ group)
        is_banned = Column(Boolean)  # Is account banned

    class LevelData(Base):  # used in StorageProviderDatabase
        __tablename__ = "level_data_table"

        id = Column(Integer, primary_key=True)

        level_id = Column(Text)  # Level id
        level_data = Column(LargeBinary)  # Leve data without checksum
        level_checksum = Column(Text)  # SHA-1 HMAC checksum

        # Store the decoded level data and checksum separately to reduce database usage

    async def create_columns(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_level(self, name: str, style: int, environment: int, tag_1: int, tag_2: int, author: str,
                        level_id: str, non_latin: bool, testing_client: bool, description: str):
        # add level metadata into database
        level = self.Level(name=name, likes=0, dislikes=0, plays=0, deaths=0, clears=0,
                           style=style, environment=environment, tag_1=tag_1, tag_2=tag_2,
                           date=datetime.date.today(), author=author,
                           level_id=level_id, non_latin=non_latin, record_user='', record=0,
                           testing_client=testing_client, description=description, featured=False)
        async with self.session.begin() as session:
            session.add(level)
            await session.commit()

    async def update_user(self, user: User):
        async with self.session.begin() as session:
            session.add(user)
            await session.commit()

    async def add_user(self, username: str, password_hash: str, user_id: str):
        # register user
        user = self.User(username=username, password_hash=password_hash, user_id=user_id, uploads=0, is_admin=False,
                         is_mod=False, is_booster=False, is_valid=True, is_banned=False)
        async with self.session.begin() as session:
            session.add(user)
            await session.commit()

    async def execute_selection(self, selection) -> list:
        async with self.session.begin() as session:
            return (await session.execute(
                selection
            )).scalars().all()

    async def get_like_type(self, level: Level, username: str) -> str:
        # get user's like type (like or dislike or none) of a level
        async with self.session.begin() as session:
            like = (await session.execute(
                select(self.LikeUsers).where(self.LikeUsers.parent_id == level.id,
                                             self.LikeUsers.username == username)
            )).scalars().first()
            dislike = (await session.execute(
                select(self.DislikeUsers).where(self.DislikeUsers.parent_id == level.id,
                                                self.DislikeUsers.username == username)
            )).scalars().first()
            if like is not None:
                return '0'  # like
            elif dislike is not None:
                return '1'  # dislike
            else:
                return '3'  # none

    async def add_like_to_level(self, username: str, level: Level):
        # add like to level
        async with self.session.begin() as session:
            like = self.LikeUsers(parent_id=level.id, username=username)
            level.likes += 1
            session.add_all([like, level])
            await session.commit()

    async def add_dislike_to_level(self, username: str, level: Level):
        # add dislike to level
        async with self.session.begin() as session:
            dislike = self.DislikeUsers(parent_id=level.id, username=username)
            level.dislikes += 1
            session.add_all([dislike, level])
            await session.commit()

    async def add_play_to_level(self, level: Level):
        # add play to level
        async with self.session.begin() as session:
            level.plays += 1
            session.add(level)
            await session.commit()

    async def add_death_to_level(self, level: Level):
        # add death to level
        async with self.session.begin() as session:
            level.deaths += 1
            session.add(level)
            await session.commit()

    async def add_clear_to_level(self, username: str, level: Level):
        # add clear to level
        async with self.session.begin() as session:
            if (await session.execute(
                    select(self.ClearedUsers).where(self.ClearedUsers.parent_id == level.id,
                                                    self.ClearedUsers.username == username)
            )).scalars().first() is None:
                clear = self.ClearedUsers(parent_id=level.id, username=username)
                session.add(clear)
            level.clears += 1
            session.add(level)
            await session.commit()

    async def update_record_to_level(self, username: str, level: Level, record: int):
        # update record to level
        async with self.session.begin() as session:
            level.record_user = username
            level.record = record
            session.add(level)
            await session.commit()

    async def get_user_from_username(self, username: str) -> User | None:
        # get user from username
        async with self.session.begin() as session:
            user = (await session.execute(
                select(self.User).where(self.User.username == username)
            )).scalars().first()
            return user if (user is not None) else None

    async def get_user_from_user_id(self, user_id: str) -> User | None:
        # get user from user id
        async with self.session.begin() as session:
            user = (await session.execute(
                select(self.User).where(self.User.user_id == user_id)
            )).scalars().first()
            return user if (user is not None) else None

    async def get_level_from_level_id(self, level_id: str) -> Level | None:
        # get level from level id
        async with self.session.begin() as session:
            level = (await session.execute(
                select(self.Level).where(self.Level.level_id == level_id)
            )).scalars().first()
            return level if (level is not None) else None

    async def get_clear_type(self, level: Level, username: str) -> str:
        # get user's clear type (yes or no) of a level
        async with self.session.begin() as session:
            clear = (await session.execute(
                select(self.ClearedUsers).where(self.ClearedUsers.parent_id == level.id,
                                                self.ClearedUsers.username == username)
            )).scalars().first()
            if clear is not None:
                return 'yes'
            else:
                return 'no'

    async def get_liked_levels_by_user(self, username: str) -> list[LikeUsers]:
        # get user's liked levels
        async with self.session.begin() as session:
            return (
                await session.execute(
                    select(self.LikeUsers).where(self.LikeUsers.username == username)
                )
            ).scalars().all()

    async def get_disliked_levels_by_user(self, username: str) -> list[DislikeUsers]:
        # get user's disliked levels
        async with self.session.begin() as session:
            return (
                await session.execute(
                    select(self.DislikeUsers).where(self.LikeUsers.username == username)
                )
            ).scalars().all()

    async def add_level_data(self, level_id: str, level_data, level_checksum: str):
        # add level data into database as bytes
        if isinstance(level_data, str):
            level_data = level_data.encode()
        async with self.session.begin() as session:
            level_data_item = self.LevelData(
                level_id=level_id,
                level_data=level_data,
                level_checksum=level_checksum
            )
            session.add(level_data_item)
            await session.commit()

    async def dump_level_data(self, level_id: str) -> LevelData | None:
        async with self.session.begin() as session:
            level_data_item = (await session.execute(
                select(self.LevelData).where(self.LevelData.level_id == level_id)
            )).scalars().first()
            if level_data_item is not None:
                return level_data_item
            else:
                return None

    async def delete_level(self, level: Level):
        async with self.session.begin() as session:
            session.delete(level)
            await session.execute(
                delete(self.LikeUsers).where(self.LikeUsers.parent_id == level.id)
            )
            await session.execute(
                delete(self.DislikeUsers).where(self.LikeUsers.parent_id == level.id)
            )
            await session.commit()

    async def delete_level_data(self, level_id: str):
        async with self.session.begin() as session:
            level_data_item = (await session.execute(
                self.LevelData.where(self.LevelData.level_id == level_id)
            )).scalars().first()
            level_data_item.delete()
            session.add(level_data_item)
            await session.commit()

    async def set_featured(self, level: Level, is_featured: bool):
        async with self.session.begin() as session:
            level.featured = is_featured
            session.add(level)
            await session.commit()

    async def get_level_count(self, selection=None) -> int:
        if selection is None:
            selection = select(self.Level)
        async with self.session.begin() as session:
            return (
                await session.execute(
                    select(func.count()).select_from(selection)
                )
            ).scalars().first()

    async def get_player_count(self) -> int:
        async with self.session.begin() as session:
            return (
                await session.execute(
                    select(func.count()).select_from(self.User)
                )
            ).scalars().first()

    # Code below are for migration

    class Stats(Base):
        __tablename__ = "stats_table"

        id = Column(Integer, primary_key=True)

        level_id = Column(Text)  # Level id
        likes_users = Column(Text)
        dislikes_users = Column(Text)

    async def get_old_stats(self) -> list[Stats]:
        async with self.session.begin() as session:
            return (
                await session.execute(
                    select(self.Stats)
                )
            ).scalars().all()

    async def add_like_user_only(self, level: Level, username: str):
        async with self.session.begin() as session:
            like = self.LikeUsers(parent_id=level.id, username=username)
            session.add(like)
            await session.commit()

    async def add_dislike_user_only(self, level: Level, username: str):
        async with self.session.begin() as session:
            dislike = self.DislikeUsers(parent_id=level.id, username=username)
            session.add(dislike)
            await session.commit()
