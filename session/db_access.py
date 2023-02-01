from sqlalchemy.ext.asyncio import AsyncSession
from session.models import Session
from sqlalchemy import select
from common import ClientType


class SessionDBAccessLayer:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_session_by_id(self, session_id: int) -> Session | None:
        return (await self.db_session.execute(
            select(Session).where(Session.id == session_id)
        )).scalars().first()

    async def get_session_by_user_id(self, user_id: int) -> Session | None:
        return (await self.db_session.execute(
            select(Session).where(Session.user_id == user_id)
        )).scalars().first()

    async def new_session(
            self,
            username: str,
            user_id: int,
            mobile: bool,
            client_type: ClientType,
            locale: str
    ) -> Session:
        # Drop existing session
        existing_session = await self.get_session_by_user_id(user_id)
        if existing_session is not None:
            await self.db_session.delete(existing_session)
        session = Session(
            username=username,
            user_id=user_id,
            mobile=mobile,
            type=client_type.value,
            locale=locale
        )
        self.db_session.add(session)
        await self.db_session.commit()
        return session

    async def commit(self):
        await self.db_session.commit()
