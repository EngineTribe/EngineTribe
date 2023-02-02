from pydantic import BaseModel as PydanticModel
import json


class Session(PydanticModel):
    session_id: str
    username: str
    user_id: int  # User ID
    mobile: bool  # Is mobile client
    client_type: int  # Client types
    locale: str  # Client locale

    def serialize(self) -> str:
        return json.dumps(
            self.dict(),
            separators=(',', ':')
        )


def deserialize_session(data: str) -> Session:
    return Session.parse_obj(
        json.loads(data)
    )
