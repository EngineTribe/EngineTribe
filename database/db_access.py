from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Level, LevelData, User, ClearedUsers, LikeUsers, DislikeUsers, Client
import datetime
from sqlalchemy import func, select, delete
from sqlalchemy import or_, and_
from config import RECORD_CLEAR_USERS


class DBAccessLayer:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_level(self, name: str, style: int, environment: int, tag_1: int, tag_2: int, author_id: int,
                        level_id: str, non_latin: bool, testing_client: bool, description: str):
        # add level metadata into database
        level = Level(name=name, likes=0, dislikes=0, plays=0, deaths=0, clears=0,
                      style=style, environment=environment, tag_1=tag_1, tag_2=tag_2,
                      date=datetime.date.today(), author_id=author_id,
                      level_id=level_id, non_latin=non_latin, record_user_id=0, record=0,
                      testing_client=testing_client, featured=False, description=description)
        self.session.add(level)
        await self.session.flush()
        return level

    async def update_user(self, user: User):
        self.session.add(user)
        await self.session.flush()

    async def add_user(self, username: str, password_hash: str, im_id: int):
        # register user
        user = User(username=username, password_hash=password_hash, im_id=im_id, uploads=0, is_admin=False,
                    is_mod=False, is_booster=False, is_valid=True, is_banned=False)

        self.session.add(user)
        await self.session.flush()

    async def execute_selection(self, selection) -> list:
        return (await self.session.execute(
            selection
        )).scalars().all()

    async def get_like_type(self, level: Level, user_id: int) -> str:
        # get user's like type (like or dislike or none) of a level
        like = (await self.session.execute(
            select(LikeUsers).where(and_(LikeUsers.parent_id == level.id,
                                    LikeUsers.user_id == user_id))
        )).scalars().first()
        dislike = (await self.session.execute(
            select(DislikeUsers).where(and_(DislikeUsers.parent_id == level.id,
                                       DislikeUsers.user_id == user_id))
        )).scalars().first()
        if like is not None:
            return '0'  # like
        elif dislike is not None:
            return '1'  # dislike
        else:
            return '3'  # none

    async def add_like_to_level(self, user_id: int, level: Level):
        # add like to level
        like = LikeUsers(parent_id=level.id, user_id=user_id)
        level.likes += 1
        self.session.add_all([like, level])
        await self.session.flush()

    async def add_dislike_to_level(self, user_id: int, level: Level):
        # add dislike to level
        dislike = DislikeUsers(parent_id=level.id, user_id=user_id)
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

    async def add_clear_to_level(self, user_id: int, level: Level):
        # add clear to level
        if RECORD_CLEAR_USERS:
            if (await self.session.execute(
                    select(ClearedUsers).where(and_(ClearedUsers.parent_id == level.id,
                                               ClearedUsers.user_id == user_id))
            )).scalars().first() is None:
                clear = ClearedUsers(parent_id=level.id, user_id=user_id)
                self.session.add(clear)
        level.clears += 1
        self.session.add(level)
        await self.session.flush()

    async def update_record_to_level(self, user_id: int, level: Level, record: int):
        # update record to level
        level.record_user_id = user_id
        level.record = record
        self.session.add(level)
        await self.session.flush()

    async def get_user_by_username(self, username: str) -> User | None:
        # get user from username
        user = (await self.session.execute(
            select(User).where(User.username == username)
        )).scalars().first()
        return user if (user is not None) else None

    async def get_user_by_id(self, user_id: int) -> User | None:
        # get user from id
        user = (await self.session.execute(
            select(User).where(User.id == user_id)
        )).scalars().first()
        return user if (user is not None) else None

    async def get_user_by_im_id(self, im_id: int) -> User | None:
        # get user from IM user id
        user = (await self.session.execute(
            select(User).where(User.im_id == im_id)
        )).scalars().first()
        return user if (user is not None) else None

    async def get_level_by_level_id(self, level_id: str) -> Level | None:
        # get level from level id
        level = (await self.session.execute(
            select(Level).where(Level.level_id == level_id)
        )).scalars().first()
        return level if (level is not None) else None

    async def get_clear_type(self, level: Level, user_id: int) -> str:
        # get user's clear type (yes or no) of a level
        if RECORD_CLEAR_USERS:
            clear = (await self.session.execute(
                select(ClearedUsers).where(and_(ClearedUsers.parent_id == level.id,
                                           ClearedUsers.user_id == user_id))
            )).scalars().first()
            if clear is not None:
                return 'yes'
            else:
                return 'no'
        else:
            return 'no'

    async def get_liked_levels_by_user(self, user_id: int) -> list[LikeUsers]:
        # get user's liked levels
        return (
            await self.session.execute(
                select(LikeUsers).where(LikeUsers.user_id == user_id)
            )
        ).scalars().all()

    async def get_disliked_levels_by_user(self, user_id: int) -> list[DislikeUsers]:
        # get user's disliked levels
        return (
            await self.session.execute(
                select(DislikeUsers).where(DislikeUsers.user_id == user_id)
            )
        ).scalars().all()

    async def get_cleared_levels_by_user(self, user_id: int) -> list[ClearedUsers]:
        # get user's cleared levels
        return (
            await self.session.execute(
                select(ClearedUsers).where(ClearedUsers.user_id == user_id)
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
            delete(DislikeUsers).where(DislikeUsers.parent_id == level.id)
        )
        await self.session.flush()

    async def delete_level_data(self, level_id: str):
        await self.session.execute(
            delete(LevelData).where(LevelData.level_id == level_id)
        )
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

    async def get_client_by_token(self, token: str) -> Client | None:
        return (await self.session.execute(
            select(Client).where(Client.token == token)
        )).scalars().first()

    async def get_all_clients(self) -> list[Client]:
        return (await self.session.execute(
            select(Client)
        )).scalars().all()

    async def new_client(self, token: str, client_type: int, locale: str, mobile: bool, proxied: bool):
        client = Client(
            token=token,
            type=client_type,
            locale=locale,
            mobile=mobile,
            proxied=proxied,
            valid=True
        )
        self.session.add(client)
        await self.session.flush()


    async def revoke_client(self, client: Client):
        client.valid = False
        self.session.add(client)
        await self.session.flush()

    async def delete_client(self, client: Client):
        await self.session.delete(client)
        await self.session.flush()

    async def commit(self):
        await self.session.commit()
