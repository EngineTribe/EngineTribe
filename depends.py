from contextvars import ContextVar
from typing import Union

from fastapi import Header, HTTPException

from models import ErrorMessage

connection_count = ContextVar("connection_count", default=0)


def connection_count_inc():
    connection_count.set(connection_count.get() + 1)


def is_valid_user(user_agent: Union[str, None] = Header(default=None)):
    is_vaild_ua = False
    if user_agent is not None:
        is_vaild_ua = True
    if (
            ("GameMaker" in user_agent)  # Windows / Linux
            or ("Android" in user_agent)  # Android
            or ("EngineBot" in user_agent)  # Engine Bot
            or ("PlayStation" in user_agent)  # PlayStation Vita
    ):
        is_vaild_ua = True
    if not is_vaild_ua:
        raise HTTPException(
            status_code=200,
            detail=ErrorMessage(error_type="005", message="Illegal client."),
        )
