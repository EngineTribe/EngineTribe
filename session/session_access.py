from session.models import Session, deserialize_session
from redis.asyncio import Redis
from common import ClientType
from time import time

from locales import get_locale_model

'''
Redis 1: session:{session_id} -> Session
Redis 2: user_id -> session_id
'''


def generate_session_id(user_id: int):
    return hex(int(f"{user_id}{str(int(time()))[2:]}")).upper()[2:]


async def new_session(
        redis_1: Redis,
        redis_2: Redis,
        username: str,
        user_id: int,
        mobile: bool,
        client_type: ClientType,
        locale: str
) -> Session:
    session = Session(
        session_id=generate_session_id(user_id),
        username=username,
        user_id=user_id,
        mobile=mobile,
        client_type=client_type.value,
        locale=locale
    )
    # Drop previous session
    await drop_session_by_id(
        redis_1,
        await get_session_id_by_user_id(redis_2, user_id)
    )
    # Add new session
    async with redis_1.pipeline(transaction=True) as pipe:
        await pipe.set(
            f"session:{session.session_id}",
            session.serialize(),
            ex=60 * 60 * 24  # 1 day
        ).execute()
    # Add user_id -> session_id
    async with redis_2.pipeline(transaction=True) as pipe:
        await pipe.set(
            user_id,
            session.session_id,
        ).execute()
    return session


async def get_session_by_id(
        redis_1: Redis,
        session_id: str
) -> Session | None:
    session_data = await redis_1.get(f"session:{session_id}")
    if session_data is None:
        return None
    return deserialize_session(session_data.decode())


async def get_session_data(
        redis_1: Redis,
        session_id: str
) -> tuple:
    session_data = await get_session_by_id(redis_1, session_id)
    if session_data is None:
        return None, None, None
    else:
        return session_data, ClientType(session_data.client_type), get_locale_model(session_data.locale)


async def drop_session_by_id(
        redis_1: Redis,
        session_id: str
) -> bool:
    if (await redis_1.exists(f"session:{session_id}")):
        async with redis_1.pipeline(transaction=True) as pipe:
            await pipe.delete(f"session:{session_id}").execute()
        return True
    else:
        return False


async def get_session_id_by_user_id(
        redis_2: Redis,
        user_id: int
) -> str | None:
    return await redis_2.get(user_id)
