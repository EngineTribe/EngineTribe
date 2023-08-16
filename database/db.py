from config import *
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    AsyncAttrs,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
import ssl


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Database:
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
        self.async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )

        # Store the decoded level data and checksum separately to reduce database usage

    async def create_columns(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
