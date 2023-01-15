from fastapi import APIRouter, Form, Depends

from context import db
from config import API_KEY
from depends import connection_count_inc
from models import (
    UserInfoRequestBody,
    UpdatePasswordRequestBody,
    UpdatePermissionRequestBody,
    RegisterRequestBody,
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
import smmwe_lib

from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK
)

router = APIRouter(prefix="/user", dependencies=[Depends(connection_count_inc)])


@router.post("/login")
async def user_login_handler(
        alias: str = Form(""),
        token: str = Form(""),
        password: str = Form(""),
):  # User login
    # match auth_code to generate token
    tokens_auth_code_match = {
        smmwe_lib.Tokens.PC_CN: f"{alias}|PC|CN",
        smmwe_lib.Tokens.PC_ES: f"{alias}|PC|ES",
        smmwe_lib.Tokens.PC_EN: f"{alias}|PC|EN",
        smmwe_lib.Tokens.Mobile_CN: f"{alias}|MB|CN",
        smmwe_lib.Tokens.Mobile_ES: f"{alias}|MB|ES",
        smmwe_lib.Tokens.Mobile_EN: f"{alias}|MB|EN",
        smmwe_lib.Tokens.PC_Legacy_CN: f"{alias}|PC|CN|L",
        smmwe_lib.Tokens.PC_Legacy_ES: f"{alias}|PC|ES|L",
        smmwe_lib.Tokens.PC_Legacy_EN: f"{alias}|PC|EN|L",
        smmwe_lib.Tokens.Mobile_Legacy_CN: f"{alias}|MB|CN|L",
        smmwe_lib.Tokens.Mobile_Legacy_ES: f"{alias}|MB|ES|L",
        smmwe_lib.Tokens.Mobile_Legacy_EN: f"{alias}|MB|EN|L",
        smmwe_lib.Tokens.PC_Testing_CN: f"{alias}|PC|CN|T",
        smmwe_lib.Tokens.PC_Testing_ES: f"{alias}|PC|ES|T",
        smmwe_lib.Tokens.PC_Testing_EN: f"{alias}|PC|EN|T",
        smmwe_lib.Tokens.Mobile_Testing_CN: f"{alias}|MB|CN|T",
        smmwe_lib.Tokens.Mobile_Testing_ES: f"{alias}|MB|ES|T",
        smmwe_lib.Tokens.Mobile_Testing_EN: f"{alias}|MB|EN|T",
    }

    password = password.encode("latin1").decode("utf-8")
    # Fix for Starlette
    # https://github.com/encode/starlette/issues/425

    # match the token
    try:
        auth_code = tokens_auth_code_match[token]
        auth_data = smmwe_lib.parse_auth_code(auth_code)
    except KeyError:
        return ErrorMessage(error_type="003", message="Illegal client.")

    mobile: bool = True if "MB" in token else False

    user = await db.get_user_from_username(username=alias)
    if user is None:
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
    if user.password_hash != smmwe_lib.calculate_password_hash(password):
        return ErrorMessage(
            error_type="007", message=auth_data.locale_item.ACCOUNT_ERROR_PASSWORD
        )
    if "|L" in auth_code:
        # 3.1.x return data
        return LegacyUserLoginProfile(
            alias=alias,
            id=user.user_id,
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
            id=user.user_id,
            uploads=user.uploads,
            mobile=mobile,
            auth_code=auth_code,
        )


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs

@router.post("/register")  # Register account
async def user_register_handler(request: RegisterRequestBody):
    if request.api_key != API_KEY:
        return APIKeyErrorMessage(api_key=request.api_key)
    expected_user = await db.get_user_from_user_id(user_id=request.user_id)
    if expected_user is not None:
        return UserErrorMessage(
            error_type="035",
            message="User ID already exists.",
            user_id=request.user_id,
            username=expected_user.username
        )
    expected_user = await db.get_user_from_username(username=request.username)
    if expected_user is not None:
        return UserErrorMessage(
            error_type="036",
            message="Username already exists.",
            user_id=request.user_id,
            username=expected_user.username
        )
    await db.add_user(
        username=request.username,
        password_hash=request.password_hash,
        user_id=request.user_id
    )
    return UserSuccessMessage(
        success="Registration success.",
        username=request.username,
        user_id=request.user_id,
        type="register"
    )


@router.post("/update_permission")  # Update permission
async def user_set_permission_handler(request: UpdatePermissionRequestBody) -> ErrorMessage | UserSuccessMessage:
    # username/user_id, permission, value, api_key
    if request.api_key != API_KEY:
        return APIKeyErrorMessage(api_key=request.api_key)

    if request.username:
        user = await db.get_user_from_username(username=request.username)
        if user is None:
            return UserErrorMessage(
                error_type="006",
                message="User not found.",
                username=request.username
            )
    elif request.user_id:
        user = await db.get_user_from_user_id(user_id=request.user_id)
        if user is None:
            return UserErrorMessage(
                error_type="006",
                message="User not found.",
                user_id=request.user_id
            )
    else:
        return ErrorMessage(error_type="255", message="API error.")

    # key permission changed (mod or booster)
    # if changed then push to bots
    key_permission_changed: bool = False

    match request.permission:
        case "mod":
            if user.is_mod != request.value:
                key_permission_changed = True
            user.is_mod = request.value

        case "admin":
            user.is_admin = request.value

        case "booster":
            if user.is_booster != request.value:
                key_permission_changed = True
            user.is_booster = request.value

        case "valid":
            user.is_valid = request.value

        case "banned":
            user.is_banned = request.value

        case _:
            return ErrorMessage(error_type="255", message="Permission does not exist.")

    await db.update_permissions_to_user(user=user)

    if key_permission_changed:
        if ENABLE_ENGINE_BOT_WEBHOOK:
            if request.permission == 'booster':
                await smmwe_lib.push_to_engine_bot_qq({
                    'type': 'permission_change',
                    'permission': 'booster',
                    'username': user.username,
                    'value': request.value
                })
            elif request.permission == 'mod':
                await smmwe_lib.push_to_engine_bot_qq({
                    'type': 'permission_change',
                    'permission': 'mod',
                    'username': user.username,
                    'value': request.value
                })
        if ENABLE_DISCORD_WEBHOOK:
            if request.permission == 'booster':
                await smmwe_lib.push_to_engine_bot_discord(
                    f"{'🤗' if request.value else '😥'} "
                    f"**{user.username}** ahora {'sí' if request.value else 'no'} "
                    f"tiene el rol **Booster** en Engine Kingdom!! "
                )
            elif request.permission == 'mod':
                await smmwe_lib.push_to_engine_bot_discord(
                    f"{'🤗' if request.value else '😥'} "
                    f"**{user.username}** ahora {'sí' if request.value else 'no'} "
                    f"tiene el rol **Stage Moderator** en Engine Kingdom!! "
                )
    return UserPermissionSuccessMessage(
        success="Permission updated.",
        type="update",
        username=user.username,
        user_id=user.user_id,
        permission=request.permission,
        value=request.value
    )


@router.post("/update_password")  # Update password
async def user_update_password_handler(request: UpdatePasswordRequestBody) -> ErrorMessage | UserSuccessMessage:
    # username, password_hash, api_key
    if request.api_key != API_KEY:
        return APIKeyErrorMessage(api_key=request.api_key)
    user = await db.get_user_from_username(username=request.username)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found.",
            username=request.username
        )
    if user.user_id == request.user_id:
        user.password_hash = request.password_hash
        await db.update_user(user=user)
        return UserSuccessMessage(
            success="Update password success.",
            type="update",
            username=user.username,
            user_id=user.user_id
        )
    else:
        return ErrorMessage(error_type='006', message='User incorrect.')


@router.post("/info")  # Get user info
async def user_info_handler(request: UserInfoRequestBody):
    if request.username:
        user = await db.get_user_from_username(username=request.username)
        if user is None:
            return UserErrorMessage(
                error_type="006",
                message="User not found.",
                username=request.username
            )
    elif request.user_id:
        user = await db.get_user_from_user_id(user_id=request.user_id)
        if user is None:
            return UserErrorMessage(
                error_type="006",
                message="User not found.",
                user_id=request.user_id
            )
    else:
        return ErrorMessage(error_type="255", message="API error.")
    return UserInfoMessage(
        result=UserInfo(
            username=user.username,
            user_id=user.user_id,
            uploads=user.uploads,
            is_admin=user.is_admin,
            is_mod=user.is_mod,
            is_booster=user.is_booster,
            is_valid=user.is_valid,
            is_banned=user.is_banned
        )
    )