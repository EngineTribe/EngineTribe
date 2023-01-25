from pydantic import BaseModel as PydanticModel
from typing import Optional, Union


class ErrorMessage(PydanticModel):
    error_type: str
    message: str


class APIKeyErrorMessage(ErrorMessage):
    error_type: str = "004"
    message: str = "Invalid API key."
    api_key: str


class UserErrorMessage(ErrorMessage):
    user_id: Optional[str | int]
    username: Optional[str]


class StageSuccessMessage(PydanticModel):
    success: str
    type: Optional[str] = "stage"
    id: Optional[str]


class UserSuccessMessage(PydanticModel):
    success: str
    type: Optional[str] = "user"
    username: Optional[str]
    user_id: Optional[str]


class UserPermissionSuccessMessage(UserSuccessMessage):
    permission: str
    value: bool


class UserLoginProfile(PydanticModel):
    username: str
    admin: bool
    mod: bool
    booster: bool
    goomba: Optional[bool] = True
    alias: str
    id: str
    uploads: int
    mobile: bool
    auth_code: str


class LegacyUserLoginProfile(PydanticModel):
    alias: str
    id: str
    goomba: Optional[bool] = True
    auth_code: str
    ip: Optional[str] = "127.0.0.1"


class UserInfo(PydanticModel):
    username: str
    user_id: str
    uploads: int
    is_admin: bool
    is_mod: bool
    is_booster: bool
    is_valid: bool
    is_banned: bool


class UserInfoMessage(PydanticModel):
    type: Optional[str] = "user"
    result: UserInfo


class LevelDetailsUserData(PydanticModel):
    completed: str
    liked: str


class LevelDetails(PydanticModel):
    name: str
    likes: int
    dislikes: int
    comments: Optional[int] = 0
    intentos: int
    muertes: int
    victorias: int
    apariencia: int
    entorno: int
    etiquetas: str
    featured: int
    user_data: LevelDetailsUserData
    record: dict[str, Union[str, int]]
    date: str
    author: str
    descripcion: str
    archivo: str
    id: str


class DetailedSearchResults(PydanticModel):
    type: Optional[str] = "detailed_search"
    num_rows: int
    rows_perpage: int
    pages: int
    result: list[LevelDetails]


class SingleLevelDetails(PydanticModel):
    type: Optional[str] = "id"
    result: LevelDetails


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
    user_id: str | int


class UpdatePermissionRequestBody(PydanticModel):
    api_key: str
    username: Optional[str]
    user_id: Optional[str | int]
    permission: str
    value: bool


class UpdatePasswordRequestBody(PydanticModel):
    api_key: str
    username: str
    password_hash: str
    user_id: str | int


class UserInfoRequestBody(PydanticModel):
    username: Optional[str]
    user_id: Optional[str | int]
