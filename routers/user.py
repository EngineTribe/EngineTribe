from typing import Any

import peewee
from fastapi import APIRouter, Header, Form, Depends

from context import db
from config import API_KEY
from depends import connection_count_inc
from models import (
    UserInfoRequestBody,
    UpdatePasswordRequestBody,
    UpdatePermissionRequestBody,
    RegisterRequestBody,
    ErrorMessage
)
import smmwe_lib

import discord
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
    }

    password = password.encode("latin1").decode("utf-8")
    # Fix for Starlette
    # https://github.com/encode/starlette/issues/425

    # match the token
    try:
        auth_code = tokens_auth_code_match[token]
        auth_data = smmwe_lib.parse_auth_code(auth_code)
    except KeyError:
        return ErrorMessage(error_type="005", message="Illegal client.")

    if "SMMWEMB" in token:
        mobile = True
    else:
        mobile = False

    try:
        account = db.User.get(db.User.username == alias)
    except peewee.DoesNotExist:
        return ErrorMessage(
            error_type="006", message=auth_data.locale_item.ACCOUNT_NOT_FOUND
        )
    if not account.is_valid:
        return ErrorMessage(
            error_type="011", message=auth_data.locale_item.ACCOUNT_IS_NOT_VALID
        )
    if account.is_banned:
        return ErrorMessage(
            error_type="005", message=auth_data.locale_item.ACCOUNT_BANNED
        )
    if account.password_hash != smmwe_lib.calculate_password_hash(password):
        return ErrorMessage(
            error_type="007", message=auth_data.locale_item.ACCOUNT_ERROR_PASSWORD
        )
    if "|L" in auth_code:
        # 3.1.5 return data
        login_user_profile = {
            "goomba": True,
            "alias": alias,
            "id": account.user_id,
            "auth_code": auth_code,
            "ip": "127.0.0.1",
        }
    else:
        login_user_profile = {
            "username": alias,
            "admin": account.is_admin,
            "mod": account.is_mod,
            "booster": account.is_booster,
            "goomba": True,
            "alias": alias,
            "id": account.user_id,
            "uploads": str(account.uploads),
            "mobile": mobile,
            "auth_code": auth_code,
        }
    return login_user_profile


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs
# noinspection PyBroadException
@router.post("/register")  # Register account
async def user_register_handler(request: RegisterRequestBody):
    if request.api_key != API_KEY:
        return {
            "error_type": "004",
            "message": "Invalid API key.",
            "api_key": request.api_key,
        }
    user_exist = True
    try:
        expected_user = db.User.get(db.User.user_id == request.user_id)
    except peewee.DoesNotExist:
        user_exist = False
    if user_exist:
        return {
            "error_type": "035",
            "message": "User ID already exists.",
            "user_id": request.user_id,
            "username": expected_user.username
        }
    user_exist = True
    try:
        expected_user = db.User.get(db.User.username == request.username)
    except peewee.DoesNotExist:
        user_exist = False
    if user_exist:
        return {
            "error_type": "036",
            "message": "Username already exists.",
            "user_id": expected_user.user_id,
            "username": request.username
        }
    try:
        db.add_user(
            username=request.username,
            user_id=request.user_id,
            password_hash=request.password_hash,
        )
        return {
            "success": "Registration success.",
            "username": request.username,
            "user_id": request.user_id,
            "type": "register",
        }
    except Exception as e:
        return ErrorMessage(error_type="255", message=str(e))


@router.post("/update_permission")  # Update permission
async def user_set_permission_handler(request: UpdatePermissionRequestBody):
    # username/user_id, permission, value, api_key
    if request.api_key != API_KEY:
        return {
            "error_type": "004",
            "message": "Invalid API key.",
            "api_key": request.api_key,
        }
    try:
        if request.username:
            user = db.User.get(db.User.username == request.username)
        elif request.user_id:
            user = db.User.get(db.User.user_id == request.user_id)
        else:
            return ErrorMessage(error_type="255", message="API error.")
    except peewee.DoesNotExist:
        return ErrorMessage(error_type="006", message="User not found.")
    permission_changed: bool = False
    if request.permission == "mod":
        if user.is_mod != request.value:
            permission_changed = True
        user.is_mod = request.value
    elif request.permission == "admin":
        user.is_admin = request.value
    elif request.permission == "booster":
        if user.is_booster != request.value:
            permission_changed = True
        user.is_booster = request.value
    elif request.permission == "valid":
        user.is_valid = request.value
    elif request.permission == "banned":
        user.is_banned = request.value
    else:
        return ErrorMessage(error_type="255", message="Permission does not exist.")
    user.save()
    if permission_changed:
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
                    f"**{user.username}** ahora {'sí' if request.value else 'no'} "
                    f"tiene el rol **Booster** en Engine Kingdom!! "
                    f"{'🤗' if request.value else '😥'}\n"
                )
            elif request.permission == 'mod':
                await smmwe_lib.push_to_engine_bot_discord(
                    f"**{user.username}** ahora {'sí' if request.value else 'no'} "
                    f"tiene el rol **Stage Moderator** en Engine Kingdom!! "
                    f"{'🤗' if request.value else '😥'}\n"
                )
    return {
        "success": "Update success",
        "type": "update",
        "user_id": user.user_id,
        "username": user.username,
        "permission": request.permission,
        "value": request.value,
    }


@router.post("/update_password")  # Update password
async def user_update_password_handler(request: UpdatePasswordRequestBody):
    # username, password_hash, api_key
    if request.api_key != API_KEY:
        return {
            "error_type": "004",
            "message": "Invalid API key.",
            "api_key": request.api_key,
        }
    try:
        user = db.User.get(db.User.username == request.username)
    except peewee.DoesNotExist:
        return ErrorMessage(error_type="006", message="User not found.")
    if user.user_id == request.user_id:
        user.password_hash = request.password_hash
        user.save()
        return {"success": "Update success", "type": "update", "username": user.username}
    else:
        return ErrorMessage(error_type='006', message='User incorrect.')


@router.post("/info")  # Get user info
async def user_info_handler(request: UserInfoRequestBody):
    try:
        if request.username:
            user = db.User.get(db.User.username == request.username)
        elif request.user_id:
            user = db.User.get(db.User.user_id == request.user_id)
        else:
            return ErrorMessage(error_type="255", message="API error.")
    except peewee.DoesNotExist:
        return ErrorMessage(error_type="006", message="User not found.")
    if isinstance(user, ErrorMessage):
        return user
    return {
        "type": "user",
        "result": {
            "user_id": user.user_id,
            "username": user.username,
            "uploads": int(user.uploads),
            "is_admin": user.is_admin,
            "is_mod": user.is_mod,
            "is_booster": user.is_booster,
            "is_valid": user.is_valid,
            "is_banned": user.is_banned,
        },
    }
