from config import DATABASE_DEBUG
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class SessionDatabase:
    def __init__(self):
        url: str = "sqlite+aiosqlite://"
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=DATABASE_DEBUG, future=True,
        )
        # Base.metadata.create_all(self.engine)
        self.async_session: sessionmaker = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

        # Store the decoded level data and checksum separately to reduce database usage

    async def create_columns(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)