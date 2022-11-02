import context

from fastapi import Header, HTTPException

from models import ErrorMessage


def connection_count_inc():
    context.connection_count += 1
    print(context.connection_count)


def is_valid_user(user_agent: str | None = Header(default=None)):
    if user_agent is None or not (
            ("GameMaker" in user_agent)  # Windows / Linux
            or ("Android" in user_agent)  # Android
            or ("EngineBot" in user_agent)  # Engine Bot
            or ("PlayStation" in user_agent)  # PlayStation Vita
    ):
        raise HTTPException(
            status_code=200,
            detail=ErrorMessage(error_type="005", message="Illegal client."),
        )
