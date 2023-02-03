from fastapi import Header, Request
from typing import Optional
from config import VERIFY_USER_AGENT

from database.db_access import DBAccessLayer
from session.session_access import get_session_by_id
from models import ErrorMessageException


def is_valid_user(user_agent: str | None = Header(default=None)):
    if VERIFY_USER_AGENT:
        if user_agent is None or not (
                ("GameMaker" in user_agent)  # PC
                or ("Dalvik" in user_agent)  # Android
                or ("Android" in user_agent)  # Android
                or ("EngineBot" in user_agent)  # Engine Bot
                or ("PlayStation" in user_agent)  # PlayStation Vita
                or ("libcurl-agent" in user_agent)  # GMS2 (3.3.0+) PC
        ):
            raise ErrorMessageException(
                error_type="005",
                message="Illegal client.")
    else:
        if user_agent is None:
            raise ErrorMessageException(
                error_type="005",
                message="Illegal client.")


async def create_dal(request: Request):
    async with request.app.state.db.async_session() as session:
        async with session.begin():
            yield DBAccessLayer(session)


async def verify_and_get_session(request: Request):
    auth_code = (await request.form()).get("auth_code")
    if auth_code is None:
        raise ErrorMessageException(
            error_type="034",
            message="Permission denied."
        )
    session = await get_session_by_id(request.app.state.redis, auth_code)
    if session is None:
        raise ErrorMessageException(
            error_type="002",
            message="Session expired."
        )
    return session
