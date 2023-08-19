from fastapi import Form, Depends, Request
from routers.api_router import APIRouter

from config import API_KEY
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
from locales import get_locale_model
from common import (
    ClientType,
    calculate_password_hash,
)
from push import (
    push_to_engine_bot,
    push_to_engine_bot_discord
)
from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK,
    DISCORD_SERVER_NAME
)
from database.db_access import DBAccessLayer
from database.models import User, Client
from session.models import Session
from session.session_access import (
    get_session_by_id,
    new_session
)
from depends import (
    create_dal,
    connection_count_inc
)

router = APIRouter(
    prefix="/user",
    dependencies=[Depends(connection_count_inc)]
)


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
        request: Request,
        alias: str = Form(""),
        token: str = Form(""),
        password: str = Form(""),
        dal: DBAccessLayer = Depends(create_dal)
):
    # User login
    password = password.encode("latin1").decode("utf-8")
    # Fix for Starlette
    # https://github.com/encode/starlette/issues/425

    # match the token
    client: Client | None = await dal.get_client_by_token(token=token)
    if (client is None) or (not client.valid):
        return ErrorMessage(error_type="003", message="Illegal client.")
    locale_model = get_locale_model(client.locale)

    client_type = ClientType(client.type)

    if client_type == ClientType.ENGINE_BOT:
        user: User = User(
            id=0,
            username="EngineBot",
            im_id=0,
            password_hash="",
            uploads=0,
            is_valid=True,
            is_banned=False,
            is_admin=False,
            is_mod=True,
            is_booster=False,
        )
        user_id = 0
    else:
        user: User = await dal.get_user_by_username(username=alias)
        user_id: int = user.id if user else 0

    if client_type != ClientType.ENGINE_BOT:
        if user_id == 0:
            return ErrorMessage(
                error_type="006", message=locale_model.ACCOUNT_NOT_FOUND
            )
        if not user.is_valid:
            return ErrorMessage(
                error_type="011", message=locale_model.ACCOUNT_IS_NOT_VALID
            )
        if user.is_banned:
            return ErrorMessage(
                error_type="005", message=locale_model.ACCOUNT_BANNED
            )
        if user.password_hash != calculate_password_hash(password):
            return ErrorMessage(
                error_type="007", message=locale_model.ACCOUNT_ERROR_PASSWORD
            )

    # add session to redis
    client_type = ClientType(client.type)
    session = await new_session(
        redis=request.app.state.redis,
        username=user.username,
        user_id=user_id,
        mobile=client.mobile,
        client_type=client_type,
        locale=client.locale,
        proxied=client.proxied
    )
    auth_code: str = session.session_id

    if client_type is ClientType.LEGACY:
        # 3.1.x return data
        return LegacyUserLoginProfile(
            alias=alias,
            id=user.im_id,
            auth_code=auth_code,
            goomba=True,
            ip=request.client.host
        )
    else:
        return UserLoginProfile(
            username=alias,
            admin=user.is_admin,
            mod=user.is_mod,
            booster=user.is_booster,
            goomba=True,
            alias=alias,
            id=str(user.im_id),
            uploads=user.uploads,
            mobile=client.mobile,
            auth_code=auth_code,
        )


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs

@router.post("/register")  # Register account
async def user_register_handler(
        api_key: str = Form(),
        im_id: int = Form(),
        username: str = Form(),
        password_hash: str = Form(),
        dal: DBAccessLayer = Depends(create_dal)
):
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    expected_user = await dal.get_user_by_im_id(im_id=im_id)
    if expected_user is not None:
        return UserErrorMessage(
            error_type="035",
            message="User ID already exists.",
            im_id=str(im_id),
            username=expected_user.username
        )
    expected_user = await dal.get_user_by_username(username=username)
    if expected_user is not None:
        return UserErrorMessage(
            error_type="036",
            message="Username already exists.",
            im_id=str(im_id),
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
        im_id=str(im_id),
        type="register"
    )


@router.post("/{user_identifier}/permission/{permission}")  # Update permission
async def user_set_permission_handler(
        user_identifier: str,
        permission: str,
        api_key: str = Form(),
        value: bool = Form(False),
        dal: DBAccessLayer = Depends(create_dal)
):
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
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
                await push_to_engine_bot({
                    'type': 'permission_change',
                    'permission': 'booster',
                    'username': user.username,
                    'value': value
                })
            elif permission == 'mod':
                await push_to_engine_bot({
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
                    f"tiene el rol **Booster** en {DISCORD_SERVER_NAME}!! "
                )
            elif permission == 'mod':
                await push_to_engine_bot_discord(
                    f"{'🤗' if value else '😥'} "
                    f"**{user.username}** ahora {'sí' if value else 'no'} "
                    f"tiene el rol **Stage Moderator** en {DISCORD_SERVER_NAME}!! "
                )
    return UserPermissionSuccessMessage(
        success="Permission updated.",
        type="update",
        username=user.username,
        im_id=str(user.im_id),
        permission=permission,
        value=value
    )


@router.post("/{user_identifier}/update_password")  # Update password
async def user_update_password_handler(
        user_identifier: str,
        im_id: int = Form(),
        password_hash: str = Form(),
        api_key: str = Form(),
        dal: DBAccessLayer = Depends(create_dal)
):
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
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
            im_id=str(user.im_id)
        )
    else:
        return ErrorMessage(error_type='006', message='User incorrect.')


@router.post("/{user_identifier}/info")  # Get user info
async def user_info_handler(
        user_identifier: str,
        dal: DBAccessLayer = Depends(create_dal)
):
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
