from pydantic import BaseModel as PydanticModel
from typing import Optional


class ErrorMessage(PydanticModel):
    error_type: str
    message: str


class RegisterRequestBody(PydanticModel):
    api_key: str
    username: str
    password_hash: str
    user_id: str


class UpdatePermissionRequestBody(PydanticModel):
    username: Optional[str]
    user_id: Optional[str]
    permission: Optional[str]
    value: Optional[str]


class UserInfoRequestBody(PydanticModel):
    username: Optional[str]
    user_id: Optional[str]