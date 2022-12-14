import datetime
import logging
import re
from math import ceil

import aiohttp
import peewee
from fastapi import APIRouter, Form, Depends
from fastapi.responses import RedirectResponse, Response
from typing import Optional

from context import db, storage
import dfa_filter
from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK,
    ENABLE_ENGINE_BOT_COUNTER_WEBHOOK,
    BOOSTERS_EXTRA_LIMIT,
    UPLOAD_LIMIT,
    OFFENSIVE_WORDS_FILTER,
    ROWS_PERPAGE,
)
from depends import connection_count_inc, is_valid_user
from locales import es_ES  # for fallback messages
from models import ErrorMessage
from smmwe_lib import (
    parse_auth_code,
    strip_level,
    gen_level_id_md5,
    gen_level_id_sha1,
    gen_level_id_sha256,
    level_db_to_dict,
    push_to_engine_bot_qq,
    push_to_engine_bot_discord
)

router = APIRouter(
    prefix="/stage",
    dependencies=[Depends(connection_count_inc), Depends(is_valid_user)],
)


# router.post("s/detailed_search") == stages/detailed_search
@router.post("s/detailed_search")
async def stages_detailed_search_handler(
        auth_code: str = Form("EngineBot|PC|CN"),
        featured: Optional[str] = Form(None),
        page: Optional[str] = Form("1"),
        title: Optional[str] = Form(None),
        author: Optional[str] = Form(None),
        aparience: Optional[str] = Form(None),
        entorno: Optional[str] = Form(None),
        last: Optional[str] = Form(None),
        sort: Optional[str] = Form(None),
        liked: Optional[str] = Form(None),
        disliked: Optional[str] = Form(None),
        historial: Optional[str] = Form(None),
        dificultad: Optional[str] = Form(None),
) -> ErrorMessage | dict:  # Detailed search (level list)
    if title:
        title = title.encode("latin1").decode("utf-8")
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    auth_data = parse_auth_code(auth_code)

    results = []
    levels = db.Level.select()

    # Filter and search

    if featured:
        match featured:
            case "promising":
                levels = levels.where(db.Level.featured == True).order_by(db.Level.id.desc())  # featured levels
                levels = levels  # latest levels
            case "popular":
                levels = levels.order_by(
                    (db.Level.likes - db.Level.dislikes).desc()
                )  # likes
            case _:
                return ErrorMessage(error_type="031", message=auth_data.locale_item.UNKNOWN_QUERY_MODE)
    else:
        levels = levels.order_by(db.Level.id.desc())  # latest levels

    # avoid non-testing client error
    if not auth_data.testing_client:
        levels = levels.where(db.Level.testing_client == False)

    mobile: bool = True if auth_data.platform == "MB" else False

    if not page:
        page = 1
    else:
        page = int(page)

    # detailed search
    if title:
        levels = levels.where(db.Level.name.contains(title))
    if author:
        levels = levels.where(db.Level.author == author)
    if aparience:
        levels = levels.where(db.Level.style == aparience)
    if entorno:
        levels = levels.where(db.Level.environment == entorno)
    if last:
        days = int(last.strip("d"))
        levels = levels.where(
            db.Level.date.between(
                datetime.date.today() + datetime.timedelta(days=-days),
                datetime.date.today(),
            )
        )
    if sort:
        if sort == "antiguos":
            levels = levels.order_by(db.Level.id.asc())
        else:
            return ErrorMessage(error_type="031", message=auth_data.locale_item.UNKNOWN_QUERY_MODE)
    if liked:
        stats = db.Stats.select().where(
            db.Stats.likes_users.contains(auth_data.username)
        )
        # Engine Tribe stores the username of the liker instead of the ID, so the username in auth_code is used here
        level_ids = []
        for stat in stats:
            level_ids.append(stat.level_id)
        levels = levels.where(db.Level.level_id.in_(level_ids))
    elif disliked:
        stats = db.Stats.select().where(
            db.Stats.dislikes_users.contains(auth_data.username)
        )
        level_ids = []
        for stat in stats:
            level_ids.append(stat.level_id)
        levels = levels.where(db.Level.level_id.in_(level_ids))

    if dificultad:
        levels = levels.where(db.Level.deaths != 0)
        match dificultad:
            case "0":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.8, 1000.0))  # Easy
            case "1":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.5, 0.8))  # Normal
            case "2":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.3, 0.5))  # Hard
            case "3":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.0, 0.3))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=auth_data.locale_item.UNKNOWN_DIFFICULTY)

    if historial:
        return ErrorMessage(
            error_type="255", message=auth_data.locale_item.NOT_IMPLEMENTED
        )

    # calculate numbers
    num_rows = len(levels)
    if num_rows > ROWS_PERPAGE:
        rows_perpage = ROWS_PERPAGE
        pages = ceil(num_rows / ROWS_PERPAGE)
    else:
        rows_perpage = num_rows
        pages = 1
    for level in levels.paginate(page, rows_perpage):
        try:
            like_type = db.get_like_type(
                level_id=level.level_id, username=auth_data.username
            )
            results.append(
                level_db_to_dict(
                    level_data=level,
                    locale=auth_data.locale,
                    generate_url_function=storage.generate_url,
                    mobile=mobile,
                    like_type=like_type,
                )
            )
        except Exception as e:
            print(e)
    if len(results) == 0:
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found
    else:
        return {
            "type": "detailed_search",
            "num_rows": str(num_rows),
            "rows_perpage": str(rows_perpage),
            "pages": str(pages),
            "result": results,
        }


@router.post("/{level_id}/stats/likes")
async def stats_likes_handler(
        level_id: str,
        auth_code: str = Form(),
) -> dict:
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except peewee.DoesNotExist:
        stat = db.Stats(level_id=level_id, likes_users="", dislikes_users="")
    stat.likes_users += username + ","
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.likes += 1
    level.save()
    if level.likes == 100 or level.likes == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"???? Felicidades, el **{level.name}** de **{level.author}** tiene **{level.likes}** me gusta!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.likes}_likes",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return {"success": "success", "id": level_id, "type": "stats"}


@router.post("/{level_id}/stats/dislikes", dependencies=[Depends(is_valid_user)])
async def stats_dislikes_handler(
        level_id: str,
        auth_code: str = Form(),
) -> dict:
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except peewee.DoesNotExist:
        stat = db.Stats(level_id=level_id, likes_users="", dislikes_users="")
    stat.dislikes_users += username + ","
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.dislikes += 1
    level.save()
    return {"success": "success", "id": level_id, "type": "stats"}


@router.post("/upload")
async def stages_upload_handler(
        auth_code: str = Form(),
        swe: str = Form(),
        name: str = Form(),
        aparience: str = Form(),
        entorno: str = Form(),
        tags: str = Form(),
) -> ErrorMessage | dict:
    auth_data = parse_auth_code(auth_code)
    account = db.User.get(db.User.username == auth_data.username)

    if account.is_booster:
        upload_limit = UPLOAD_LIMIT + BOOSTERS_EXTRA_LIMIT
    elif account.is_mod or account.is_admin:
        upload_limit = 999  # Almost infinite
    else:
        upload_limit = UPLOAD_LIMIT
    if account.uploads >= upload_limit:
        return ErrorMessage(
            error_type="025",
            message=auth_data.locale_item.UPLOAD_LIMIT_REACHED + f"({upload_limit})",
        )

    name = name.encode("latin1").decode("utf-8")
    tags = tags.encode("latin1").decode("utf-8")
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    print("Uploading level " + name)

    if OFFENSIVE_WORDS_FILTER:  # Apply filter
        name_filtered = dfa_filter.DFAFilter().filter(name)
        if name_filtered != name.lower():
            name = name_filtered

    # check non-Latin
    non_latin = False
    if re.sub("[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]", "", name) != name:
        non_latin = True

    # check testing client
    testing_client: bool = True if auth_data.testing_client else False

    # generate level id
    swe_to_generate = strip_level(swe)
    level_id = gen_level_id_md5(swe_to_generate)

    # check duplicated level ID
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except peewee.DoesNotExist:
        print("md5: Not duplicated")
        not_duplicated = True
    if not not_duplicated:
        print("md5: duplicated, fallback to sha1")
        level_id = gen_level_id_sha1(swe_to_generate)

    if not not_duplicated:
        # if duplicated again then use sha256
        try:
            db.Level.get(db.Level.level_id == level_id)
        except peewee.DoesNotExist:
            print("sha1: Not duplicated")
            not_duplicated = True
        if not not_duplicated:
            print("sha1: duplicated, fallback to sha256")
            level_id = gen_level_id_sha256(swe_to_generate)

    if not not_duplicated:
        # if sha256 duplicated again then return error
        try:
            db.Level.get(db.Level.level_id == level_id)
        except peewee.DoesNotExist:
            print("sha256: Not duplicated")
            not_duplicated = True
        if not not_duplicated:
            return ErrorMessage(
                error_type="009", message=auth_data.locale_item.LEVEL_ID_REPEAT
            )

    if len(swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return ErrorMessage(
            error_type="026", message=auth_data.locale_item.FILE_TOO_LARGE
        )
    try:
        await storage.upload_file(
            level_data=swe, level_id=level_id
        )  # Upload to storage backend
    except ConnectionError:
        return ErrorMessage(
            error_type="010", message=auth_data.locale_item.UPLOAD_CONNECT_ERROR
        )

    db.add_level(
        name,
        aparience,
        entorno,
        tags,
        auth_data.username,
        level_id,
        non_latin,
        testing_client,
    )  # add new level to database
    account.uploads += 1
    account.save()  # add a upload to account info
    if ENABLE_DISCORD_WEBHOOK:
        await push_to_engine_bot_discord(
            f'???? **{auth_data.username}** subi?? un nuevo nivel: **{name}**\n'
            f'> ID: `{level_id}`  Tags: `{tags.split(",")[0].strip()}, {tags.split(",")[1].strip()}`\n'
            f'> Descargar: {storage.generate_download_url(level_id=level_id)}'
        )
    if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
        await push_to_engine_bot_qq({
            "type": "new_arrival",
            "level_id": level_id,
            "level_name": name,
            "author": auth_data.username,
        })
    return {
        "success": auth_data.locale_item.UPLOAD_COMPLETE,
        "id": level_id,
        "type": "upload",
    }


@router.post("/random")
async def stage_id_random_handler(
        auth_code: str = Form("EngineBot|PC|CN"),
        dificultad: Optional[str] = Form(None)
) -> ErrorMessage | dict:  # Random level
    auth_data = parse_auth_code(auth_code)
    if auth_data.platform == "MB":
        mobile = True  # Mobile fixes
    else:
        mobile = False
    levels = db.Level.select()
    if dificultad:
        levels = levels.where(db.Level.deaths != 0)
        match dificultad:
            case "0":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.8, 1000.0))  # Easy
            case "1":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.5, 0.8))  # Normal
            case "2":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.3, 0.5))  # Hard
            case "3":
                levels = levels.where((db.Level.clears / db.Level.deaths).between(0.0, 0.3))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=auth_data.locale_item.UNKNOWN_DIFFICULTY)
    if db.db_type == "mysql":
        level = levels.order_by(peewee.fn.Rand()).limit(1)[0]
    else:
        level = (
            levels.order_by(peewee.fn.Random()).limit(1)[0]
        )  # postgresql and sqlite
    like_type = db.get_like_type(level_id=level.level_id, username=auth_data.username)
    return {
        "type": "id",
        "result": level_db_to_dict(
            level_data=level,
            locale=auth_data.locale,
            generate_url_function=storage.generate_url,
            mobile=mobile,
            like_type=like_type,
        ),
    }


@router.post("/{level_id}")
async def stage_id_search_handler(
        level_id: str,
        auth_code: str = Form("EngineBot|PC|CN")
) -> ErrorMessage | dict:  # Level ID search
    auth_data = parse_auth_code(auth_code)
    try:
        mobile: bool = True if auth_data.platform == "MB" else False

        level = db.Level.get(db.Level.level_id == level_id)
        like_type = db.get_like_type(
            level_id=level.level_id, username=auth_data.username
        )
        return {
            "type": "id",
            "result": level_db_to_dict(
                level_data=level,
                locale=auth_data.locale,
                generate_url_function=storage.generate_url,
                mobile=mobile,
                like_type=like_type,
            ),
        }
    except Exception as ex:
        print(ex)
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found


@router.get("/{level_id}/file")
async def stage_file_handler(level_id: str) -> Response | RedirectResponse:  # Return level data
    match storage.type:
        case 'onedrive-cf':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'onemanager':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'database':
            return Response(
                content=storage.dump_level_data(level_id=level_id),
                headers={
                    'Content-Disposition': f'attachment; '
                                           f'filename="{db.Level.get(db.Level.level_id == level_id).name}.swe"'
                },
                media_type='text/plain'
            )


@router.post("/{level_id}/delete")
async def stage_delete_handler(level_id: str) -> dict:  # Delete level
    level = db.Level.get(db.Level.level_id == level_id)
    db.Level.delete().where(db.Level.level_id == level_id).execute()
    user = db.User.get(db.User.username == level.author)
    user.uploads -= 1
    user.save()
    return {"success": "success", "id": level_id, "type": "stage"}


@router.post("/{level_id}/switch/promising")
async def switch_promising_handler(level_id: str) -> dict:
    # Switch featured (promising) level
    level = db.Level.get(db.Level.level_id == level_id)
    if not level.featured:
        level.featured = True
        level.save()
        print(level_id + " added to featured")
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"???? El **{level.name}** por **{level.author}** se agrega a niveles prometedores! \n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": "new_featured",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    else:
        level.featured = False
        level.save()
        print(level_id + " removed from featured")
    return {"success": "success", "id": level_id, "type": "stage"}


@router.post("/{level_id}/stats/intentos")
async def stats_intentos_handler(level_id: str) -> ErrorMessage | dict:
    try:
        level = db.Level.get(db.Level.level_id == level_id)
    except peewee.DoesNotExist:
        logging.error(f'intentos handler: {level_id} not found')
        return ErrorMessage(error_type="029", message=es_ES.LEVEL_NOT_FOUND)
    level.plays += 1
    level.save()
    if level.plays == 100 or level.plays == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"???? Felicidades, el **{level.name}** de **{level.author}** ha sido reproducido **{level.plays}** veces!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.plays}_plays",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return {"success": "success", "id": level_id, "type": "stats"}


@router.post("/{level_id}/stats/victorias")
async def stats_victorias_handler(
        level_id: str,
        tiempo: str = Form(),
        auth_code: str = Form("EngineBot|PC|CN"),
) -> ErrorMessage | dict:
    try:
        level = db.Level.get(db.Level.level_id == level_id)
    except peewee.DoesNotExist:
        logging.error(f'victorias handler: {level_id} not found')
        return ErrorMessage(error_type="029", message=es_ES.LEVEL_NOT_FOUND)
    level.clears += 1
    level.save()
    auth_data = parse_auth_code(auth_code)
    new_record = int(tiempo)
    if level.record == 0 or level.record > new_record:
        level.record_user = auth_data.username
        level.record = new_record
        level.save()
    if level.clears == 100 or level.clears == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"???? Felicidades, el **{level.name}** de **{level.author}** ha salido victorioso **{level.clears}** veces!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.clears}_clears",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return {"success": "success", "id": level_id, "type": "stats"}


@router.post("/{level_id}/stats/muertes")
async def stats_muertes_handler(level_id: str) -> ErrorMessage | dict:
    try:
        level = db.Level.get(db.Level.level_id == level_id)
    except peewee.DoesNotExist:
        logging.error(f'muertes handler: {level_id} not found')
        return ErrorMessage(error_type="029", message=es_ES.LEVEL_NOT_FOUND)
    level.deaths += 1
    level.save()
    if level.deaths == 100 or level.deaths == 1000:
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.deaths}_deaths",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return {"success": "success", "id": level_id, "type": "stats"}


@router.get("/{level_id}/file")
async def legacy_stage_file(level_id: str) -> ErrorMessage | dict:
    try:
        async with aiohttp.request("GET", storage.generate_url(level_id)) as r:
            text = await r.text()
        return {"data": text}
    except Exception as ex:
        print(ex)
        return ErrorMessage(
            error_type="029", message=es_ES.LEVEL_NOT_FOUND
        )  # No level found
