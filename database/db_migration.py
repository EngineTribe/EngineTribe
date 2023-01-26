from sqlalchemy.ext.asyncio import AsyncSession
from database.models import *
import datetime
from sqlalchemy import func, select, delete


class DBMigrationAccessLayer:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Code below are for migration

    #     async def get_old_stats(self) -> list[Stats]:
    #         return (
    #             await self.session.execute(
    #                 select(Stats)
    #             )
    #         ).scalars().all()

    async def add_like_user_only(self, parent_id: int, user_id: int):
        like = LikeUsers(parent_id=parent_id, user_id=user_id)
        self.session.add(like)

    async def add_dislike_user_only(self, parent_id: int, user_id: int):
        dislike = DislikeUsers(parent_id=parent_id, user_id=user_id)
        self.session.add(dislike)

    async def add_clear_user_only(self, parent_id: int, user_id: int):
        clear = ClearedUsers(parent_id=parent_id, user_id=user_id)
        self.session.add(clear)

    async def get_all_level_datas_in(self, range_from, limit) -> list[LevelData]:
        # use offset
        return (await self.session.execute(
            select(LevelData).offset(range_from).limit(limit)
        )).scalars().all()

    async def get_all_old_users(self) -> list[OldUser]:
        return (await self.session.execute(
            select(OldUser)
        )).scalars().all()

    async def get_all_old_levels(self) -> list[OldLevel]:
        return (await self.session.execute(
            select(OldLevel)
        )).scalars().all()

    async def get_all_old_level_datas(self) -> list[OldLevelData]:
        return (await self.session.execute(
            select(OldLevelData)
        )).scalars().all()

    async def get_all_old_likes(self) -> list[OldLikeUsers]:
        return (await self.session.execute(
            select(OldLikeUsers)
        )).scalars().all()

    async def get_all_old_dislikes(self) -> list[OldDislikeUsers]:
        return (await self.session.execute(
            select(OldDislikeUsers)
        )).scalars().all()

    async def get_all_old_clears(self) -> list[OldClearedUsers]:
        return (await self.session.execute(
            select(OldClearedUsers)
        )).scalars().all()

    async def get_old_level_from_parent_id(self, level_id: int) -> OldLevel:
        return (await self.session.execute(
            select(OldLevel).where(OldLevel.id == level_id)
        )).scalars().first()

    async def add_user(self, username: str, password_hash: str, im_id: int, uploads: int, is_admin: bool,
                       is_mod: bool, is_booster: bool, is_valid: bool, is_banned: bool):
        # register user
        user = User(username=username, password_hash=password_hash, im_id=im_id, uploads=uploads, is_admin=is_admin,
                    is_mod=is_mod, is_booster=is_booster, is_valid=is_valid, is_banned=is_banned)
        self.session.add(user)
        await self.session.flush()

    async def add_level(self, name: str, style: int, environment: int, tag_1: int, tag_2: int, author_id: int,
                        level_id: str, non_latin: bool, testing_client: bool, record_user_id: int, record: int,
                        likes: int, dislikes: int, plays: int, deaths: int, clears: int):
        # add level metadata into database
        level = Level(name=name, likes=likes, dislikes=dislikes, plays=plays, deaths=deaths, clears=clears,
                      style=style, environment=environment, tag_1=tag_1, tag_2=tag_2,
                      date=datetime.date.today(), author_id=author_id,
                      level_id=level_id, non_latin=non_latin, record_user_id=record_user_id, record=record,
                      testing_client=testing_client, featured=False)
        self.session.add(level)
        await self.session.flush()

    async def delete_level(self, level_id: int):
        # remove level metadata from database
        await self.session.execute(
            delete(Level).where(Level.id == level_id)
        )

    async def delete_level_data(self, level_id: str):
        # remove level data from database
        await self.session.execute(
            delete(LevelData).where(LevelData.level_id == level_id)
        )

    async def delete_stats(self, level_id):
        await self.session.execute(
            delete(LikeUsers).where(LikeUsers.parent_id == level_id)
        )
        await self.session.execute(
            delete(DislikeUsers).where(DislikeUsers.parent_id == level_id)
        )

    async def get_all_levels(self) -> list[Level]:
        return (await self.session.execute(
            select(Level)
        )).scalars().all()
