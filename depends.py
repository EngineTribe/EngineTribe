import context

from fastapi import Header
from typing import Optional

from models import ErrorMessageException


def connection_count_inc():
    context.connection_count += 1


def is_valid_user(user_agent: str | None = Header(default=None)):
    # if user_agent is None or not (
    #         ("GameMaker" in user_agent)  # Windows / Linux
    #         or ("Dalvik" in user_agent)  # Android
    #         or ("Android" in user_agent)  # Android
    #         or ("EngineBot" in user_agent)  # Engine Bot
    #         or ("PlayStation" in user_agent)  # PlayStation Vita
    #         or ("libcurl-agent" in user_agent)  # GMS2 (3.3.0+) Windows / Linux
    # ):
    if user_agent is None:
        raise ErrorMessageException(
            error_type="005",
            message="Illegal client.")
