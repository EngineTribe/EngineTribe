from fastapi import APIRouter, Form, Depends

from context import db
from config import API_KEY
from depends import connection_count_inc
from models import (
    ErrorMessage,
    UserErrorMessage,
    APIKeyErrorMessage,
    UserSuccessMessage,
    UserLoginProfile,
    LegacyUserLoginProfile,
    UserPermissionSuccessMessage,
    UserInfoMessage,
    UserInfo
)
from smmwe_lib import (
    Tokens,
    AuthCodeData,
    calculate_password_hash,
    push_to_engine_bot_qq,
    push_to_engine_bot_discord, parse_auth_code
)
from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK
)
from database.db_access import DBAccessLayer
from database.models import User

AVAILABLE_TOKENS = [
    Tokens.PC_CN, Tokens.PC_ES, Tokens.PC_EN,
    Tokens.Mobile_CN, Tokens.Mobile_ES, Tokens.Mobile_EN,
    Tokens.PC_Legacy_CN, Tokens.PC_Legacy_ES, Tokens.PC_Legacy_EN,
    Tokens.Mobile_Legacy_CN, Tokens.Mobile_Legacy_ES, Tokens.Mobile_Legacy_EN,
    Tokens.PC_Testing_CN, Tokens.PC_Testing_ES, Tokens.PC_Testing_EN,
    Tokens.Mobile_Testing_CN, Tokens.Mobile_Testing_ES, Tokens.Mobile_Testing_EN
]

router = APIRouter(prefix="/user", dependencies=[Depends(connection_count_inc)])


async def get_user_from_identifier(
        dal: DBAccessLayer,
        user_identifier: str
) -> User | None:
    if user_identifier.isnumeric():
        im_id: int = int(user_identifier)
        return await dal.get_user_by_im_id(im_id=im_id)
    else:
        username: str = user_identifier
        return await dal.get_user_by_username(username=username)


@router.post("/login")
async def user_login_handler(
        alias: str = Form(""),
        token: str = Form(""),
        password: str = Form(""),
):  # User login
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)

            password = password.encode("latin1").decode("utf-8")
            # Fix for Starlette
            # https://github.com/encode/starlette/issues/425

            # match the token
            if token not in AVAILABLE_TOKENS:
                return ErrorMessage(error_type="003", message="Illegal client.")

            mobile: bool = True if "MB" in token else False

            user: User = await dal.get_user_by_username(username=alias)
            user_id: int = user.id if user else 0

            # match auth_code to generate token
            tokens_auth_code_match = {
                Tokens.PC_CN: f"{user_id}|PC|CN",
                Tokens.PC_ES: f"{user_id}|PC|ES",
                Tokens.PC_EN: f"{user_id}|PC|EN",
                Tokens.Mobile_CN: f"{user_id}|MB|CN",
                Tokens.Mobile_ES: f"{user_id}|MB|ES",
                Tokens.Mobile_EN: f"{user_id}|MB|EN",
                Tokens.PC_Legacy_CN: f"{user_id}|PC|CN|L",
                Tokens.PC_Legacy_ES: f"{user_id}|PC|ES|L",
                Tokens.PC_Legacy_EN: f"{user_id}|PC|EN|L",
                Tokens.Mobile_Legacy_CN: f"{user_id}|MB|CN|L",
                Tokens.Mobile_Legacy_ES: f"{user_id}|MB|ES|L",
                Tokens.Mobile_Legacy_EN: f"{user_id}|MB|EN|L",
                Tokens.PC_Testing_CN: f"{user_id}|PC|CN|T",
                Tokens.PC_Testing_ES: f"{user_id}|PC|ES|T",
                Tokens.PC_Testing_EN: f"{user_id}|PC|EN|T",
                Tokens.Mobile_Testing_CN: f"{user_id}|MB|CN|T",
                Tokens.Mobile_Testing_ES: f"{user_id}|MB|ES|T",
                Tokens.Mobile_Testing_EN: f"{user_id}|MB|EN|T",
            }

            auth_code = tokens_auth_code_match[token]
            auth_data: AuthCodeData = parse_auth_code(auth_code)

            if user_id == 0:
                return ErrorMessage(
                    error_type="006", message=auth_data.locale_item.ACCOUNT_NOT_FOUND
                )
            if not user.is_valid:
                return ErrorMessage(
                    error_type="011", message=auth_data.locale_item.ACCOUNT_IS_NOT_VALID
                )
            if user.is_banned:
                return ErrorMessage(
                    error_type="005", message=auth_data.locale_item.ACCOUNT_BANNED
                )
            if user.password_hash != calculate_password_hash(password):
                return ErrorMessage(
                    error_type="007", message=auth_data.locale_item.ACCOUNT_ERROR_PASSWORD
                )
            if "|L" in auth_code:
                # 3.1.x return data
                return LegacyUserLoginProfile(
                    alias=alias,
                    id=user.im_id,
                    auth_code=auth_code,
                    goomba=True,
                    ip="127.0.0.1"
                )
            else:
                return UserLoginProfile(
                    username=alias,
                    admin=user.is_admin,
                    mod=user.is_mod,
                    booster=user.is_booster,
                    goomba=True,
                    alias=alias,
                    id=user.im_id,
                    uploads=user.uploads,
                    mobile=mobile,
                    auth_code=auth_code,
                )


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs

@router.post("/register")  # Register account
async def user_register_handler(
        api_key: str = Form(""),
        im_id: str = Form(""),
        username: str = Form(""),
        password_hash: str = Form("")
) -> ErrorMessage | UserSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    im_id: int = int(im_id)
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            expected_user = await dal.get_user_by_im_id(im_id=im_id)
            if expected_user is not None:
                return UserErrorMessage(
                    error_type="035",
                    message="User ID already exists.",
                    im_id=im_id,
                    username=expected_user.username
                )
            expected_user = await dal.get_user_by_username(username=username)
            if expected_user is not None:
                return UserErrorMessage(
                    error_type="036",
                    message="Username already exists.",
                    im_id=im_id,
                    username=expected_user.username
                )
            await dal.add_user(
                username=username,
                password_hash=password_hash,
                im_id=im_id
            )
            await dal.commit()
            return UserSuccessMessage(
                success="Registration success.",
                username=username,
                im_id=im_id,
                type="register"
            )


@router.post("/{user_identifier}/permission/{permission}")  # Update permission
async def user_set_permission_handler(
        user_identifier: str,
        permission: str,
        api_key: str = Form(""),
        value: bool = Form(False)
) -> ErrorMessage | UserSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            user: User | None = await get_user_from_identifier(user_identifier=user_identifier, dal=dal)
            if user is None:
                return ErrorMessage(
                    error_type="006",
                    message="User not found.",
                )

            # key permission changed (mod or booster)
            # if changed then push to bots
            key_permission_changed: bool = False

            match permission:
                case "mod":
                    if user.is_mod != value:
                        key_permission_changed = True
                    user.is_mod = value

                case "admin":
                    user.is_admin = value

                case "booster":
                    if user.is_booster != value:
                        key_permission_changed = True
                    user.is_booster = value

                case "valid":
                    user.is_valid = value

                case "banned":
                    user.is_banned = value

                case _:
                    return ErrorMessage(
                        error_type="255",
                        message="Permission does not exist."
                    )

            await dal.update_user(user=user)
            await dal.commit()

            if key_permission_changed:
                if ENABLE_ENGINE_BOT_WEBHOOK:
                    if permission == 'booster':
                        await push_to_engine_bot_qq({
                            'type': 'permission_change',
                            'permission': 'booster',
                            'username': user.username,
                            'value': value
                        })
                    elif permission == 'mod':
                        await push_to_engine_bot_qq({
                            'type': 'permission_change',
                            'permission': 'mod',
                            'username': user.username,
                            'value': value
                        })
                if ENABLE_DISCORD_WEBHOOK:
                    if permission == 'booster':
                        await push_to_engine_bot_discord(
                            f"{'🤗' if value else '😥'} "
                            f"**{user.username}** ahora {'sí' if value else 'no'} "
                            f"tiene el rol **Booster** en Engine Kingdom!! "
                        )
                    elif permission == 'mod':
                        await push_to_engine_bot_discord(
                            f"{'🤗' if value else '😥'} "
                            f"**{user.username}** ahora {'sí' if value else 'no'} "
                            f"tiene el rol **Stage Moderator** en Engine Kingdom!! "
                        )
            return UserPermissionSuccessMessage(
                success="Permission updated.",
                type="update",
                username=user.username,
                im_id=user.im_id,
                permission=permission,
                value=value
            )


@router.post("/{user_identifier}/update_password")  # Update password
async def user_update_password_handler(
        user_identifier: str,
        im_id: int = Form(0),
        password_hash: str = Form(""),
        api_key: str = Form(""),
) -> ErrorMessage | UserSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            user: User | None = await get_user_from_identifier(user_identifier=user_identifier, dal=dal)
            if user is None:
                return UserErrorMessage(
                    error_type="006",
                    message="User not found.",
                )
            if user.im_id == im_id:
                user.password_hash = password_hash
                await dal.update_user(user=user)
                await dal.commit()
                return UserSuccessMessage(
                    success="Update password success.",
                    type="update",
                    username=user.username,
                    user_id=user.im_id
                )
            else:
                return ErrorMessage(error_type='006', message='User incorrect.')


@router.post("/{user_identifier}/info")  # Get user info
async def user_info_handler(
        user_identifier: str
) -> ErrorMessage | UserInfoMessage:
    async with db.async_session() as session:
        async with session.begin():
            dal = DBAccessLayer(session)
            user: User | None = await get_user_from_identifier(user_identifier=user_identifier, dal=dal)
            if user is None:
                return ErrorMessage(
                    error_type="006",
                    message="User not found."
                )
            return UserInfoMessage(
                result=UserInfo(
                    username=user.username,
                    im_id=user.im_id,
                    uploads=user.uploads,
                    is_admin=user.is_admin,
                    is_mod=user.is_mod,
                    is_booster=user.is_booster,
                    is_valid=user.is_valid,
                    is_banned=user.is_banned
                )
            )
