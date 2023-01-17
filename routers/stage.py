import datetime
import re
from math import ceil

import aiohttp
from fastapi import APIRouter, Form, Depends
from fastapi.responses import RedirectResponse, Response
from typing import Optional
from sqlalchemy import select, func

from context import db, storage
import dfa_filter
from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK,
    ENABLE_ENGINE_BOT_COUNTER_WEBHOOK,
    BOOSTERS_EXTRA_LIMIT,
    UPLOAD_LIMIT,
    OFFENSIVE_WORDS_FILTER,
    ROWS_PERPAGE
)
from depends import connection_count_inc, is_valid_user
from locales import ES, parse_tag_names  # for fallback messages
from models import (
    ErrorMessage,
    StageSuccessMessage,
    LevelDetails,
    SingleLevelDetails,
    DetailedSearchResults,
    UserErrorMessage
)
from smmwe_lib import (
    parse_auth_code,
    strip_level,
    gen_level_id_md5,
    gen_level_id_sha1,
    gen_level_id_sha256,
    level_to_details,
    push_to_engine_bot_qq,
    push_to_engine_bot_discord,
    AuthCodeData
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
) -> ErrorMessage | DetailedSearchResults:  # Detailed search (level list)
    if title:
        title = title.encode("latin1").decode("utf-8")
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425
    auth_data: AuthCodeData = parse_auth_code(auth_code)

    results: list[LevelDetails] = []

    selection = select(db.Level)

    # Filter and search

    if featured:
        match featured:
            case "promising":
                # featured levels
                selection = selection.where(db.Level.featured == True).order_by(db.Level.id.desc())
            case "popular":
                # popular levels
                selection = selection.order_by((db.Level.likes - db.Level.dislikes).desc())
            case "notpromising":
                # not featured levels (post-3.3.0)
                selection = selection.where(db.Level.featured == False)
            case _:
                return ErrorMessage(error_type="031", message=auth_data.locale_item.UNKNOWN_QUERY_MODE)
    else:
        selection = selection.order_by(db.Level.id.desc())  # latest levels

    # avoid non-testing client error
    if not auth_data.testing_client:
        selection = selection.where(db.Level.testing_client == False)

    mobile: bool = True if auth_data.platform == "MB" else False

    if not page:
        page: int = 1
    else:
        page: int = int(page)

    # detailed search
    if title:
        selection = selection.where(db.Level.name.contains(title))
    if author:
        selection = selection.where(db.Level.author == author)
    if aparience:
        selection = selection.where(db.Level.style == int(aparience))
    if entorno:
        selection = selection.where(db.Level.environment == int(entorno))
    if last:
        days: int = int(last.strip("d"))
        selection = selection.where(
            db.Level.date.between(
                datetime.date.today() + datetime.timedelta(days=-days),
                datetime.date.today(),
            )
        )
    if sort:
        match sort:
            case "antiguos":
                selection = selection.order_by(db.Level.id.asc())
            case "popular":
                # post-3.3.0
                selection = selection.where(
                    db.Level.date.between(
                        datetime.date.today() + datetime.timedelta(days=-7),
                        datetime.date.today(),
                    )
                )
                selection = selection.order_by((db.Level.likes - db.Level.dislikes).desc())
            case _:
                return ErrorMessage(error_type="031", message=auth_data.locale_item.UNKNOWN_QUERY_MODE)
    if liked:
        level_data_ids: list[int] = []  # Liked levels' data ids
        for liked_data in await db.get_liked_levels_by_user(auth_data.username):
            if liked_data.parent_id not in level_data_ids:
                level_data_ids.append(liked_data.parent_id)
        selection = selection.where(db.Level.id.in_(level_data_ids))
    elif disliked:
        level_data_ids: list[int] = []  # Disliked levels' data ids
        for disliked_data in await db.get_disliked_levels_by_user(auth_data.username):
            if disliked_data.parent_id not in level_data_ids:
                level_data_ids.append(disliked_data.parent_id)
        selection = selection.where(db.Level.id.in_(level_data_ids))
    if dificultad:
        selection = selection.where(db.Level.deaths != 0)
        match dificultad:
            case "0":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.8, 1000.0))  # Easy
            case "1":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.5, 0.8))  # Normal
            case "2":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.3, 0.5))  # Hard
            case "3":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.0, 0.3))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=auth_data.locale_item.UNKNOWN_DIFFICULTY)

    if historial:
        if historial in ["0", "1"]:
            level_data_ids_cleared: list[int] = []  # Cleared levels' data ids
            for cleared_data in await db.get_cleared_levels_by_user(auth_data.username):
                if cleared_data.parent_id not in level_data_ids_cleared:
                    level_data_ids_cleared.append(cleared_data.parent_id)
            if historial == "0":  # cleared
                selection = selection.where(db.Level.id.in_(level_data_ids_cleared))
            if historial == "1":  # not cleared
                selection = selection.where(db.Level.id.not_in(level_data_ids_cleared))
        else:
            return ErrorMessage(error_type="031", message=auth_data.locale_item.UNKNOWN_QUERY_MODE)

    # get numbers
    num_rows: int = await db.get_level_count(selection)

    # pagination
    selection = selection.offset((page - 1) * ROWS_PERPAGE).limit(ROWS_PERPAGE)

    # do query
    levels = await db.execute_selection(selection)

    if num_rows > ROWS_PERPAGE:
        rows_perpage = ROWS_PERPAGE
        pages = ceil(num_rows / ROWS_PERPAGE)
    else:
        rows_perpage = num_rows
        pages = 1

    for level in levels:
        try:
            results.append(
                level_to_details(
                    level_data=level,
                    locale=auth_data.locale,
                    generate_url_function=storage.generate_url,
                    mobile=mobile,
                    like_type=await db.get_like_type(level, auth_data.username),
                    clear_type=await db.get_clear_type(level, auth_data.username)
                )
            )
        except Exception as e:
            print(e)
    if len(results) == 0:
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found
    else:
        return DetailedSearchResults(
            num_rows=str(num_rows),
            rows_perpage=str(rows_perpage),
            pages=str(pages),
            result=results
        )


@router.post("/{level_id}/stats/likes")
async def stats_likes_handler(
        level_id: str,
        auth_code: str = Form(),
) -> StageSuccessMessage | ErrorMessage:
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    level = await db.get_level_from_level_id(level_id)
    if level is not None:
        await db.add_like_to_level(username=username, level=level)
    else:
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found
    if level.likes == 100 or level.likes == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"🎉 Felicidades, el **{level.name}** de **{level.author}** tiene **{level.likes}** me gusta!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.likes}_likes",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return StageSuccessMessage(success="Successfully updated likes", type="stats", id=level_id)


@router.post("/{level_id}/stats/dislikes", dependencies=[Depends(is_valid_user)])
async def stats_dislikes_handler(
        level_id: str,
        auth_code: str = Form(),
) -> StageSuccessMessage | ErrorMessage:
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    level = await db.get_level_from_level_id(level_id)
    if level is not None:
        await db.add_dislike_to_level(username=username, level=level)
        return StageSuccessMessage(success="Successfully updated dislikes", type="stats", id=level_id)
    else:
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found


@router.post("/upload")
async def stages_upload_handler(
        auth_code: str = Form(),
        swe: str = Form(),
        name: str = Form(),
        aparience: str = Form(),
        entorno: str = Form(),
        tags: str = Form(),
        descripcion: str = Form('Sin Descripción')
) -> ErrorMessage | StageSuccessMessage:
    auth_data: AuthCodeData = parse_auth_code(auth_code)
    user = await db.get_user_from_username(username=auth_data.username)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found",
            username=auth_data.username
        )
    if user.is_booster:
        upload_limit: int = UPLOAD_LIMIT + BOOSTERS_EXTRA_LIMIT
    elif user.is_admin:
        upload_limit: int = 999  # Almost infinite
    else:
        upload_limit: int = UPLOAD_LIMIT
    if user.uploads >= upload_limit:
        return ErrorMessage(
            error_type="025",
            message=auth_data.locale_item.UPLOAD_LIMIT_REACHED + f" ({upload_limit})",
        )

    name: str = name.encode("latin1").decode("utf-8")
    tags: str = tags.encode("latin1").decode("utf-8")
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    print("Uploading level " + name)

    if OFFENSIVE_WORDS_FILTER:  # Apply filter
        name_filtered = dfa_filter.DFAFilter().filter(name)
        if name_filtered != name.lower():
            name: str = name_filtered

    # check non-Latin
    non_latin: bool = False
    if re.sub("[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]", "", name) != name:
        non_latin: bool = True

    # check testing client
    testing_client: bool = True if auth_data.testing_client else False

    if len(swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return ErrorMessage(
            error_type="026", message=auth_data.locale_item.FILE_TOO_LARGE
        )  # File too large

    # strip level
    stripped_swe: str = strip_level(swe)

    # generate level id and check if duplicate
    level_id: str = gen_level_id_md5(stripped_swe)
    if await db.get_level_from_level_id(level_id) is None:
        print("md5: not duplicated")
    else:
        print("md5: duplicated, fallback to sha1")
        level_id = gen_level_id_sha1(stripped_swe)
        if await db.get_level_from_level_id(level_id) is None:
            print("sha1: not duplicated")
        else:
            print("sha1: duplicated, fallback to sha256")
            level_id = gen_level_id_sha256(stripped_swe)
            if await db.get_level_from_level_id(level_id) is None:
                print("sha256: not duplicated")
            else:
                print("sha256: duplicated, is a duplicated level")
                return ErrorMessage(
                    error_type="009", message=auth_data.locale_item.LEVEL_ID_REPEAT
                )
    user.uploads += 1
    await db.update_user(user=user)
    try:
        await storage.upload_file(
            level_data=swe, level_id=level_id
        )  # Upload to storage provider
    except ConnectionError:
        return ErrorMessage(
            error_type="010", message=auth_data.locale_item.UPLOAD_CONNECT_ERROR
        )

    tag_1, tag_2 = parse_tag_names(tags, auth_data.locale)
    await db.add_level(
        name=name,
        style=aparience,
        environment=entorno,
        tag_1=tag_1,
        tag_2=tag_2,
        author=auth_data.username,
        level_id=level_id,
        non_latin=non_latin,
        testing_client=testing_client,
        description=descripcion
    )  # add new level to database
    if ENABLE_DISCORD_WEBHOOK:
        await push_to_engine_bot_discord(
            f'📤 **{auth_data.username}** subió un nuevo nivel: **{name}**\n'
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
    return StageSuccessMessage(success="Successfully uploaded level", type="upload", id=level_id)


@router.post("/random")
async def stage_id_random_handler(
        auth_code: str = Form("EngineBot|PC|CN"),
        dificultad: Optional[str] = Form(None)
) -> ErrorMessage | SingleLevelDetails:  # Random level
    auth_data = parse_auth_code(auth_code)
    mobile: bool = True if auth_data.platform == "MB" else False
    username: str = auth_data.username
    selection = select(db.Level).order_by(func.random()).limit(1)
    if dificultad:
        selection = selection.where(db.Level.deaths != 0)
        match dificultad:
            case "0":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.8, 1000.0))  # Easy
            case "1":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.5, 0.8))  # Normal
            case "2":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.3, 0.5))  # Hard
            case "3":
                selection = selection.where((db.Level.clears / db.Level.deaths).between(0.0, 0.3))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=auth_data.locale_item.UNKNOWN_DIFFICULTY)
    level = (await db.execute_selection(selection))[0]
    return SingleLevelDetails(
        type="random",
        result=level_to_details(
            level_data=level,
            locale=auth_data.locale,
            generate_url_function=storage.generate_url,
            mobile=mobile,
            like_type=await db.get_like_type(level=level, username=username),
            clear_type=await db.get_clear_type(level=level, username=username)
        )
    )


@router.post("/{level_id}")
async def stage_id_search_handler(
        level_id: str,
        auth_code: str = Form("EngineBot|PC|CN")
) -> ErrorMessage | SingleLevelDetails:  # Level ID search
    auth_data = parse_auth_code(auth_code)
    mobile: bool = True if auth_data.platform == "MB" else False
    username: str = auth_data.username
    level = await db.get_level_from_level_id(level_id=level_id)
    if level is not None:
        return SingleLevelDetails(
            type="id",
            result=level_to_details(
                level_data=level,
                locale=auth_data.locale,
                generate_url_function=storage.generate_url,
                mobile=mobile,
                like_type=await db.get_like_type(level=level, username=username),
                clear_type=await db.get_clear_type(level=level, username=username)
            )
        )
    else:
        return ErrorMessage(
            error_type="029", message=auth_data.locale_item.LEVEL_NOT_FOUND
        )  # No level found


@router.get("/{level_id}/file")
async def stage_file_handler(level_id: str):  # Return level data
    match storage.type:
        case 'onedrive-cf':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'onemanager':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'database':
            level_name: str = (await db.get_level_from_level_id(level_id=level_id)).name
            level_content = await storage.dump_level_data(level_id=level_id)
            if level_content is None:
                return ErrorMessage(
                    error_type="029", message=ES.LEVEL_NOT_FOUND
                )  # No level found
            return Response(
                content=level_content,
                headers={
                    'Content-Disposition': f'attachment; '
                                           f'filename="{level_name}.swe"'
                },
                media_type='text/plain'
            )


@router.post("/{level_id}/delete")
async def stage_delete_handler(level_id: str) -> StageSuccessMessage | ErrorMessage:  # Delete level
    level = await db.get_level_from_level_id(level_id)
    if level is None:
        return ErrorMessage(error_type="029", message=ES.LEVEL_NOT_FOUND)

    # get user and check exists
    user = await db.get_user_from_username(level.author)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found",
            username=level.author
        )

    # if user exists then perform db query
    await db.delete_level(level=level)
    user.uploads -= 1
    await db.update_user(user=user)

    return StageSuccessMessage(
        success="Successfully deleted level", type="stage", id=level_id
    )


@router.post("/{level_id}/switch/promising")
async def switch_promising_handler(level_id: str) -> StageSuccessMessage | ErrorMessage:
    # Switch featured (promising) level
    level = await db.get_level_from_level_id(level_id)
    if level is None:
        return ErrorMessage(error_type="029", message="Level not found")
    if not level.featured:
        await db.set_featured(level=level, is_featured=True)
        print(level_id + " added to featured")
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"🌟 El **{level.name}** por **{level.author}** se agrega a niveles prometedores! \n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": "new_featured",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
        return StageSuccessMessage(
            success="Successfully updated featured level", type="promising", id=level_id
        )
    else:
        await db.set_featured(level=level, is_featured=False)
        return StageSuccessMessage(
            success="Successfully removed featured level", type="stage", id=level_id
        )


# Temporary solution
@router.post("{level_id}/switch/promising")
async def switch_promising_330_handler(level_id: str) -> StageSuccessMessage | ErrorMessage:
    return await switch_promising_handler(level_id)


@router.post("/{level_id}/stats/intentos")
async def stats_intentos_handler(level_id: str) -> ErrorMessage | StageSuccessMessage:
    level = await db.get_level_from_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(error_type="029", message=ES.LEVEL_NOT_FOUND)
    await db.add_play_to_level(level=level)
    if level.plays == 100 or level.plays == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"🎉 Felicidades, el **{level.name}** de **{level.author}** ha sido reproducido **{level.plays}** veces!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.plays}_plays",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return StageSuccessMessage(
        success="Successfully updated plays", id=level_id, type="stats"
    )


@router.post("/{level_id}/stats/victorias")
async def stats_victorias_handler(
        level_id: str,
        tiempo: str = Form(),
        auth_code: str = Form("EngineBot|PC|CN"),
) -> ErrorMessage | StageSuccessMessage:
    level = await db.get_level_from_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(error_type="029", message=ES.LEVEL_NOT_FOUND)
    auth_data = parse_auth_code(auth_code)
    await db.add_clear_to_level(level=level, username=auth_data.username)
    new_record: int = int(tiempo)
    if level.record == 0 or level.record > new_record:
        await db.update_record_to_level(username=auth_data.username, level=level, record=new_record)
    if level.clears == 100 or level.clears == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            await push_to_engine_bot_discord(
                f"🎉 Felicidades, el **{level.name}** de **{level.author}** ha salido victorioso **{level.clears}** veces!\n"
                f"> ID: `{level_id}`"
            )
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.clears}_clears",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
    return StageSuccessMessage(
        success="Successfully updated clears", id=level_id, type="stats"
    )


@router.post("/{level_id}/stats/muertes")
async def stats_muertes_handler(level_id: str) -> ErrorMessage | StageSuccessMessage:
    level = await db.get_level_from_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(error_type="029", message=ES.LEVEL_NOT_FOUND)
    await db.add_death_to_level(level=level)
    if level.deaths == 100 or level.deaths == 1000:
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            await push_to_engine_bot_qq({
                "type": f"{level.deaths}_deaths",
                "level_id": level_id,
                "level_name": level.name,
                "author": level.author,
            })
            # No discord push of deaths xd
    return StageSuccessMessage(
        success="Successfully updated deaths", id=level_id, type="stats"
    )


'''
@router.get("/{level_id}/file")
async def legacy_stage_file(level_id: str) -> ErrorMessage | dict:
    try:
        async with aiohttp.request("GET", storage.generate_url(level_id)) as r:
            text = await r.text()
        return {"data": text}
    except Exception as ex:
        print(ex)
        return ErrorMessage(
            error_type="029", message=ES.LEVEL_NOT_FOUND
        )  # No level found
'''
