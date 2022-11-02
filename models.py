from pydantic import BaseModel as PydanticModel
from typing import Optional


class ErrorMessage(PydanticModel):
    error_type: str
    message: str


class ErrorMessageException(Exception):
    def __init__(
            self,
            error_type: str,
            message: str
    ) -> None:
        self.error_type = error_type
        self.message = message


class RegisterRequestBody(PydanticModel):
    api_key: str
    username: str
    password_hash: str
    user_id: str


class UpdatePermissionRequestBody(PydanticModel):
    api_key: str
    username: Optional[str]
    user_id: Optional[str]
    permission: str
    value: bool


class UpdatePasswordRequestBody(PydanticModel):
    api_key: str
    username: str
    password_hash: str


class UserInfoRequestBody(PydanticModel):
    username: Optional[str]
    user_id: Optional[str]
