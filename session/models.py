from pydantic import BaseModel as PydanticModel
import json


class Session(PydanticModel):
    session_id: str
    username: str
    user_id: int  # User ID
    mobile: bool  # Is mobile client
    client_type: int  # Client types
    locale: str  # Client locale
    proxied: bool  # Is proxied

    def serialize(self) -> str:
        return json.dumps(
            self.model_dump(),
            separators=(',', ':')
        )


def deserialize_session(data: str) -> Session:
    return Session.model_validate(
        json.loads(data)
    )
