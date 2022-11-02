import context

from fastapi import Header
from typing import Optional

from models import ErrorMessageException


def connection_count_inc():
    context.connection_count += 1


def is_valid_user(user_agent: str | None = Header(default=None)):
    if user_agent is None or not (
            ("GameMaker" in user_agent)  # Windows / Linux
            or ("Android" in user_agent)  # Android
            or ("EngineBot" in user_agent)  # Engine Bot
            or ("PlayStation" in user_agent)  # PlayStation Vita
    ):
        raise ErrorMessageException(
            error_type="005",
            message="Illegal client.")
