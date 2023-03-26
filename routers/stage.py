import datetime
import re
from math import ceil

from fastapi import Form, Depends, Request
from routers.api_router import APIRouter
from fastapi.responses import RedirectResponse, Response
from typing import Optional
from sqlalchemy import select, func
import aiohttp

from config import (
    ENABLE_DISCORD_WEBHOOK,
    ENABLE_DISCORD_ARRIVAL_WEBHOOK,
    ENABLE_ENGINE_BOT_WEBHOOK,
    ENABLE_ENGINE_BOT_COUNTER_WEBHOOK,
    ENABLE_ENGINE_BOT_ARRIVAL_WEBHOOK,
    BOOSTERS_EXTRA_LIMIT,
    UPLOAD_LIMIT,
    ROWS_PERPAGE,
    RECORD_CLEAR_USERS
)
from depends import (
    is_valid_user,
    create_dal,
    verify_and_get_session,
    connection_count_inc
)
from locales import parse_tag_names  # for fallback messages
from models import (
    ErrorMessage,
    StageSuccessMessage,
    LevelDetails,
    SingleLevelDetails,
    DetailedSearchResults,
    UserErrorMessage
)
from common import (
    strip_level,
    gen_level_id_md5,
    gen_level_id_sha1,
    gen_level_id_sha256,
    level_to_details,
    push_to_engine_bot_qq,
    push_to_engine_bot_discord,
    ClientType,
    get_locale_model
)
from database.db_access import DBAccessLayer
from database.models import *
from session.models import Session

router = APIRouter(
    prefix="/stage",
    dependencies=[
        Depends(is_valid_user),
        Depends(connection_count_inc)
    ],
)


async def get_author_name_by_level(level: Level, dal: DBAccessLayer) -> str:
    author_user = await dal.get_user_by_id(level.author_id)
    if author_user is None:
        return "Unknown"
    else:
        return author_user.username


async def get_record_user_name_by_level(level: Level, dal: DBAccessLayer) -> str:
    if level.record_user_id == 0:
        return "None"
    else:
        record_user = await dal.get_user_by_id(level.record_user_id)
        if record_user is None:
            return "Unknown"
        else:
            return record_user.username


# router.post("s/detailed_search") == stages/detailed_search
@router.post("s/detailed_search")
async def stages_detailed_search_handler(
        request: Request,
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
        rows_perpage: Optional[str] = Form(None),
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | DetailedSearchResults:  # Detailed search (level list)
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425
    if title:
        title = title.encode("latin1").decode("utf-8")
    storage = request.app.state.storage
    client_type = ClientType(session.client_type)
    locale_model = get_locale_model(session.locale)

    results: list[LevelDetails] = []

    # Filter and search
    selection = select(Level)

    if featured:
        match featured:
            case "promising":
                # featured levels
                selection = selection.where(Level.featured == True).order_by(Level.id.desc())
            case "popular":
                # popular levels
                selection = selection.order_by((Level.likes - Level.dislikes).desc())
            case "notpromising":
                # not featured levels (post-3.3.0)
                selection = selection.where(Level.featured == False)
            case _:
                return ErrorMessage(error_type="031", message=locale_model.UNKNOWN_QUERY_MODE)
    else:
        selection = selection.order_by(Level.id.desc())  # latest levels

    # avoid non-testing client error
    if client_type is not ClientType.TESTING:
        selection = selection.where(Level.testing_client == False)

    # convert page to int
    if not page:
        page: int = 1
    else:
        page: int = int(page)

    # detailed search
    if title:
        selection = selection.where(Level.name.contains(title))
    if author:
        _author = await dal.get_user_by_username(author)
        if _author is not None:
            author_id: int = _author.id
            selection = selection.where(Level.author_id == author_id)
        else:
            return ErrorMessage(error_type="006", message=locale_model.ACCOUNT_NOT_FOUND)
    if aparience:
        selection = selection.where(Level.style == int(aparience))
    if entorno:
        selection = selection.where(Level.environment == int(entorno))
    if last:
        days: int = int(last.strip("d"))
        selection = selection.where(
            Level.date.between(
                datetime.date.today() + datetime.timedelta(days=-days),
                datetime.date.today(),
            )
        )
    if sort:
        match sort:
            case "antiguos":
                selection = selection.order_by(Level.id.asc())
            case "popular":
                # post-3.3.0
                selection = selection.where(
                    Level.date.between(
                        datetime.date.today() + datetime.timedelta(days=-7),
                        datetime.date.today(),
                    )
                )
                selection = selection.order_by((Level.likes - Level.dislikes).desc())
            case _:
                return ErrorMessage(error_type="031", message=locale_model.UNKNOWN_QUERY_MODE)
    if liked:
        level_data_ids: list[int] = []  # Liked levels' data ids
        for liked_data in await dal.get_liked_levels_by_user(session.user_id):
            if liked_data.parent_id not in level_data_ids:
                level_data_ids.append(liked_data.parent_id)
        selection = selection.where(Level.id.in_(level_data_ids))
    elif disliked:
        level_data_ids: list[int] = []  # Disliked levels' data ids
        for disliked_data in await dal.get_disliked_levels_by_user(session.user_id):
            if disliked_data.parent_id not in level_data_ids:
                level_data_ids.append(disliked_data.parent_id)
        selection = selection.where(Level.id.in_(level_data_ids))
    if dificultad:
        selection = selection.where(Level.plays != 0)
        match dificultad:
            case "0":
                selection = selection.where((Level.clears / Level.plays).between(0.2, 10.0))  # Easy
            case "1":
                selection = selection.where((Level.clears / Level.plays).between(0.08, 0.2))  # Normal
            case "2":
                selection = selection.where((Level.clears / Level.plays).between(0.01, 0.08))  # Hard
            case "3":
                selection = selection.where((Level.clears / Level.plays).between(0.0, 0.01))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=locale_model.UNKNOWN_DIFFICULTY)
    if historial:
        if not RECORD_CLEAR_USERS:
            return ErrorMessage(error_type="255", message=locale_model.NOT_IMPLEMENTED)
        else:
            if historial in ["0", "1"]:
                level_data_ids_cleared: list[int] = []  # Cleared levels' data ids
                for cleared_data in await dal.get_cleared_levels_by_user(session.user_id):
                    if cleared_data.parent_id not in level_data_ids_cleared:
                        level_data_ids_cleared.append(cleared_data.parent_id)
                if historial == "0":  # cleared
                    selection = selection.where(Level.id.in_(level_data_ids_cleared))
                if historial == "1":  # not cleared
                    selection = selection.where(Level.id.not_in(level_data_ids_cleared))
            else:
                return ErrorMessage(error_type="031", message=locale_model.UNKNOWN_QUERY_MODE)

    # get numbers
    num_rows: int = await dal.get_level_count(selection)

    # pagination
    selection = selection.offset((page - 1) * ROWS_PERPAGE).limit(ROWS_PERPAGE)

    # do query
    levels = await dal.execute_selection(selection)

    if num_rows > ROWS_PERPAGE:
        rows_perpage: int = int(rows_perpage) if rows_perpage is not None else ROWS_PERPAGE
        pages = ceil(num_rows / rows_perpage)
    else:
        rows_perpage: int = num_rows
        pages = 1

    # get results
    for level in levels:
        try:
            author_name: str = await get_author_name_by_level(level, dal)
            record_user_name: str = await get_record_user_name_by_level(level, dal)
            if storage.type == 'discord':
                level_file_url: str = await storage.generate_url(
                    level_id=level.level_id,
                    level_db_id=level.id,
                    proxied=session.proxied
                )
            else:
                level_file_url: str = storage.generate_url(level.level_id)
            results.append(
                level_to_details(
                    level_data=level,
                    locale=session.locale,
                    level_file_url=level_file_url,
                    mobile=session.mobile,
                    like_type=await dal.get_like_type(level, session.user_id),
                    clear_type=await dal.get_clear_type(level, session.user_id),
                    author=author_name,
                    record_user=record_user_name
                )
            )
        except Exception as e:
            print(e)
    await dal.commit()
    if len(results) == 0:
        return ErrorMessage(
            error_type="029", message=locale_model.LEVEL_NOT_FOUND
        )  # No level found
    else:
        return DetailedSearchResults(
            num_rows=num_rows,
            rows_perpage=rows_perpage,
            pages=pages,
            result=results
        )


@router.post("/{level_id}/stats/likes")
async def stats_likes_handler(
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> StageSuccessMessage | ErrorMessage:
    locale_model = get_locale_model(session.locale)
    level: Level = await dal.get_level_by_level_id(level_id)
    if level is not None:
        await dal.add_like_to_level(user_id=session.user_id, level=level)
        await dal.commit()
    else:
        return ErrorMessage(
            error_type="029", message=locale_model.LEVEL_NOT_FOUND
        )  # No level found
    if level.likes == 100 or level.likes == 1000:
        if ENABLE_DISCORD_WEBHOOK or (ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK):
            author_name: str = await get_author_name_by_level(level, dal)
            if ENABLE_DISCORD_WEBHOOK:
                await push_to_engine_bot_discord(
                    f"🎉 Felicidades, el **{level.name}** de **{author_name}** tiene **{level.likes}** me gusta!\n"
                    f"> ID: `{level_id}`"
                )
            if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
                await push_to_engine_bot_qq({
                    "type": f"{level.likes}_likes",
                    "level_id": level_id,
                    "level_name": level.name,
                    "author": author_name,
                })
    return StageSuccessMessage(success="Successfully updated likes", type="stats", id=level_id)


@router.post("/{level_id}/stats/dislikes", dependencies=[Depends(is_valid_user)])
async def stats_dislikes_handler(
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        session: Session = Depends(verify_and_get_session)
) -> StageSuccessMessage | ErrorMessage:
    locale_model = get_locale_model(session.locale)
    level = await dal.get_level_by_level_id(level_id)
    if level is not None:
        await dal.add_dislike_to_level(user_id=session.user_id, level=level)
        await dal.commit()
        return StageSuccessMessage(success="Successfully updated dislikes", type="stats", id=level_id)
    else:
        return ErrorMessage(
            error_type="029", message=locale_model.LEVEL_NOT_FOUND
        )  # No level found


@router.post("/upload")
async def stages_upload_handler(
        request: Request,
        swe: str = Form(),
        name: str = Form(),
        aparience: str = Form(),
        entorno: str = Form(),
        tags: str = Form(),
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | StageSuccessMessage:
    storage = request.app.state.storage
    client_type = ClientType(session.client_type)
    locale_model = get_locale_model(session.locale)
    user: User | None = await dal.get_user_by_id(session.user_id)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found",
            user_id=session.user_id
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
            message=locale_model.UPLOAD_LIMIT_REACHED + f" ({upload_limit})",
        )

    name: str = name.encode("latin1").decode("utf-8")
    tags: str = tags.encode("latin1").decode("utf-8")
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    print("Uploading level " + name)

    # check non-Latin
    non_latin: bool = False
    if re.sub("[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]", "", name) != name:
        non_latin: bool = True

    if len(swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return ErrorMessage(
            error_type="026", message=locale_model.FILE_TOO_LARGE
        )  # File too large

    # strip level
    stripped_swe: str = strip_level(swe)

    # generate level id and check if duplicate
    level_id: str = gen_level_id_md5(stripped_swe)
    if await dal.get_level_by_level_id(level_id) is None:
        print("md5: not duplicated")
    else:
        print("md5: duplicated, fallback to sha1")
        level_id = gen_level_id_sha1(stripped_swe)
        if await dal.get_level_by_level_id(level_id) is None:
            print("sha1: not duplicated")
        else:
            print("sha1: duplicated, fallback to sha256")
            level_id = gen_level_id_sha256(stripped_swe)
            if await dal.get_level_by_level_id(level_id) is None:
                print("sha256: not duplicated")
            else:
                print("sha256: duplicated, is a duplicated level")
                return ErrorMessage(
                    error_type="009", message=locale_model.LEVEL_ID_REPEAT
                )
    user.uploads += 1
    await dal.update_user(user=user)

    if storage.type == 'discord':
        tag_1, tag_2 = parse_tag_names(tags, session.locale)
        level = await dal.add_level(
            name=name,
            style=int(aparience),
            environment=int(entorno),
            tag_1=tag_1,
            tag_2=tag_2,
            author_id=session.user_id,
            level_id=level_id,
            non_latin=non_latin,
            testing_client=(True if client_type is ClientType.TESTING else False)
        )  # add new level to database
        level_author: User = await dal.get_user_by_id(session.user_id)
        try:
            await storage.upload_file(
                level_data=swe,
                level_id=level_id,
                level_db_id=level.id,
                level_name=name,
                level_author=level_author.username,
                level_author_im_id=level_author.id,
                level_tags=tags
            )
        except ConnectionError:
            return ErrorMessage(
                error_type="010", message=locale_model.UPLOAD_CONNECT_ERROR
            )
    else:
        try:
            await storage.upload_file(
                level_data=swe, level_id=level_id
            )  # Upload to storage provider
        except ConnectionError:
            return ErrorMessage(
                error_type="010", message=locale_model.UPLOAD_CONNECT_ERROR
            )

        tag_1, tag_2 = parse_tag_names(tags, session.locale)
        await dal.add_level(
            name=name,
            style=int(aparience),
            environment=int(entorno),
            tag_1=tag_1,
            tag_2=tag_2,
            author_id=session.user_id,
            level_id=level_id,
            non_latin=non_latin,
            testing_client=(True if client_type is ClientType.TESTING else False)
        )  # add new level to database
    if ENABLE_DISCORD_WEBHOOK and ENABLE_DISCORD_ARRIVAL_WEBHOOK and storage.type != 'discord':
        await push_to_engine_bot_discord(
            f'📤 **{user.username}** subió un nuevo nivel: **{name}**\n'
            f'> ID: `{level_id}`  Tags: `{tags.split(",")[0].strip()}, {tags.split(",")[1].strip()}`\n'
            f'> Descargar: {storage.generate_download_url(level_id=level_id)}'
        )
    if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_ARRIVAL_WEBHOOK:
        await push_to_engine_bot_qq({
            "type": "new_arrival",
            "level_id": level_id,
            "level_name": name,
            "author": user.username,
        })
    await dal.commit()
    return StageSuccessMessage(success="Successfully uploaded level", type="upload", id=level_id)


@router.post("/random")
async def stage_id_random_handler(
        request: Request,
        dificultad: Optional[str] = Form(None),
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | SingleLevelDetails:  # Random level
    storage = request.app.state.storage
    locale_model = get_locale_model(session.locale)
    user_id: int = session.user_id
    selection = select(Level).order_by(func.random()).limit(1)
    if dificultad:
        selection = selection.where(Level.plays != 0)
        match dificultad:
            case "0":
                selection = selection.where((Level.clears / Level.plays).between(0.2, 10.0))  # Easy
            case "1":
                selection = selection.where((Level.clears / Level.plays).between(0.08, 0.2))  # Normal
            case "2":
                selection = selection.where((Level.clears / Level.plays).between(0.01, 0.08))  # Hard
            case "3":
                selection = selection.where((Level.clears / Level.plays).between(0.0, 0.01))  # Expert
            case _:
                return ErrorMessage(error_type="030", message=locale_model.UNKNOWN_DIFFICULTY)
    level: Level = (await dal.execute_selection(selection))[0]
    author_name: str = await get_author_name_by_level(level, dal)
    record_user_name: str = await get_record_user_name_by_level(level, dal)
    if storage.type == 'discord':
        level_file_url: str = await storage.generate_url(
            level_id=level.level_id,
            level_db_id=level.id,
            proxied=session.proxied
        )
    else:
        level_file_url: str = storage.generate_url(level.level_id)
    return SingleLevelDetails(
        type="random",
        result=level_to_details(
            level_data=level,
            locale=session.locale,
            level_file_url=level_file_url,
            mobile=session.mobile,
            like_type=await dal.get_like_type(level=level, user_id=user_id),
            clear_type=await dal.get_clear_type(level=level, user_id=user_id),
            author=author_name,
            record_user=record_user_name
        )
    )


@router.post("/{level_id}")
async def stage_id_search_handler(
        request: Request,
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | SingleLevelDetails:  # Level ID search
    storage = request.app.state.storage
    locale_model = get_locale_model(session.locale)
    user_id: int = session.user_id
    level: Level | None = await dal.get_level_by_level_id(level_id=level_id)
    if storage.type == 'discord':
        level_file_url: str = await storage.generate_url(
            level_id=level.level_id,
            level_db_id=level.id,
            proxied=session.proxied
        )
    else:
        level_file_url: str = storage.generate_url(level.level_id)
    if level is not None:
        author_name: str = await get_author_name_by_level(level, dal)
        record_user_name: str = await get_record_user_name_by_level(level, dal)
        return SingleLevelDetails(
            type="id",
            result=level_to_details(
                level_data=level,
                locale=session.locale,
                level_file_url=level_file_url,
                mobile=session.mobile,
                like_type=await dal.get_like_type(level=level, user_id=user_id),
                clear_type=await dal.get_clear_type(level=level, user_id=user_id),
                author=author_name,
                record_user=record_user_name
            )
        )
    else:
        return ErrorMessage(
            error_type="029", message=locale_model.LEVEL_NOT_FOUND
        )  # No level found


@router.get("/{level_id}/file")
async def stage_file_handler(
        request: Request,
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal)
):  # Return level data
    storage = request.app.state.storage
    match storage.type:
        case 'onedrive-cf':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'onemanager':
            return RedirectResponse(storage.generate_download_url(level_id=level_id))
        case 'database':
            level_name: str = (await dal.get_level_by_level_id(level_id=level_id)).name
            level_content = await storage.dump_level_data(level_id=level_id)
            if level_content is None:
                return ErrorMessage(
                    error_type="029", message="Level not found."
                )  # No level found
            return Response(
                content=level_content,
                headers={
                    'Content-Disposition': f'attachment; '
                                           f'filename="{level_name}.swe"'
                },
                media_type='text/plain'
            )
        case 'discord':
            level: Level | None = await dal.get_level_by_level_id(level_id=level_id)
            if level is None:
                return ErrorMessage(
                    error_type="029", message="Level not found."
                )
            async with aiohttp.request(
                    method='GET',
                    url=await storage.generate_download_url(
                        level_id=level.level_id,
                        level_db_id=level.id,
                        proxied=False
                    ),
                    headers={
                        "User-Agent": "EngineTribe"
                    }
            ) as response:
                return Response(
                    content=await response.text(),
                    headers={
                        'Content-Disposition': f'attachment; '
                                               f'filename="{level.name}.swe"'
                    },
                    media_type='text/plain'
                )


@router.post("/{level_id}/delete")
async def stage_delete_handler(
        request: Request,
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> StageSuccessMessage | ErrorMessage:  # Delete level
    storage = request.app.state.storage
    level: Level | None = await dal.get_level_by_level_id(level_id)
    if level is None:
        return ErrorMessage(
            error_type="029", message="Level not found."
        )  # No level found

    # get user and check exists
    user = await dal.get_user_by_id(level.author_id)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found",
            user_id=level.author_id
        )

    # if user exists then perform db query
    await dal.delete_level(level=level)
    user.uploads -= 1
    await dal.update_user(user=user)
    await dal.commit()
    if storage.type == 'database':
        await storage.delete_level(level_id=level_id)

    return StageSuccessMessage(
        success="Successfully deleted level", type="stage", id=level_id
    )


@router.post("/{level_id}/switch/promising")
async def switch_promising_handler(
        level_id: str,
        auth_code: str = Form(),
        dal: DBAccessLayer = Depends(create_dal),
        session: Session = Depends(verify_and_get_session)
) -> StageSuccessMessage | ErrorMessage:
    # Switch featured (promising) level
    level: Level | None = await dal.get_level_by_level_id(level_id)
    user: User | None = await dal.get_user_by_id(session.user_id)
    if user is None:
        return UserErrorMessage(
            error_type="006",
            message="User not found",
            user_id=session.user_id
        )
    if not user.is_mod:
        return ErrorMessage(
            error_type="037", message="Permission denied."
        )
    if level is None:
        return ErrorMessage(
            error_type="029", message="Level not found."
        )  # No level found
    if not level.featured:
        await dal.set_featured(level=level, is_featured=True)
        await dal.commit()
        if ENABLE_DISCORD_WEBHOOK or (ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK):
            author_name: str = await get_author_name_by_level(level, dal)
            if ENABLE_DISCORD_WEBHOOK:
                await push_to_engine_bot_discord(
                    f"🌟 El **{level.name}** por **{author_name}** se agrega a niveles prometedores! \n"
                    f"> ID: `{level_id}`"
                )
            if ENABLE_ENGINE_BOT_WEBHOOK:
                await push_to_engine_bot_qq({
                    "type": "new_featured",
                    "level_id": level_id,
                    "level_name": level.name,
                    "author": author_name,
                })
        return StageSuccessMessage(
            success="Successfully updated featured level", type="promising", id=level_id
        )
    else:
        await dal.set_featured(level=level, is_featured=False)
        await dal.commit()
        return StageSuccessMessage(
            success="Successfully removed featured level", type="stage", id=level_id
        )


# Temporary solution
@router.post("{level_id}/switch/promising")
async def switch_promising_330_handler(
        request: Request,
        level_id: str,
        auth_code: str = Form(),
        dal: DBAccessLayer = Depends(create_dal),
        session: Session = Depends(verify_and_get_session)
) -> StageSuccessMessage | ErrorMessage:
    return await switch_promising_handler(request, level_id, auth_code, dal, session)


@router.post("/{level_id}/stats/intentos")
async def stats_intentos_handler(
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | StageSuccessMessage:
    level: Level | None = await dal.get_level_by_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(
            error_type="029", message="Level not found."
        )  # No level found
    await dal.add_play_to_level(level=level)
    await dal.commit()
    if level.plays == 100 or level.plays == 1000:
        if ENABLE_DISCORD_WEBHOOK or (ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK):
            author_name: str = await get_author_name_by_level(level, dal)
            if ENABLE_DISCORD_WEBHOOK:
                await push_to_engine_bot_discord(
                    f"🎉 Felicidades, el **{level.name}** de **{author_name}** ha sido reproducido **{level.plays}** veces!\n"
                    f"> ID: `{level_id}`"
                )
            if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
                await push_to_engine_bot_qq({
                    "type": f"{level.plays}_plays",
                    "level_id": level_id,
                    "level_name": level.name,
                    "author": author_name,
                })
    return StageSuccessMessage(
        success="Successfully updated plays", id=level_id, type="stats"
    )


@router.post("/{level_id}/stats/victorias")
async def stats_victorias_handler(
        level_id: str,
        tiempo: str = Form(),
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | StageSuccessMessage:
    level: Level | None = await dal.get_level_by_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(
            error_type="029", message="Level not found."
        )  # No level found
    await dal.add_clear_to_level(level=level, user_id=session.user_id)
    new_record: int = int(tiempo)
    if level.record == 0 or level.record > new_record:
        await dal.update_record_to_level(user_id=session.user_id, level=level, record=new_record)
    await dal.commit()
    if level.clears == 100 or level.clears == 1000:
        if ENABLE_DISCORD_WEBHOOK or (ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK):
            author_name: str = await get_author_name_by_level(level, dal)
            if ENABLE_DISCORD_WEBHOOK:
                await push_to_engine_bot_discord(
                    f"🎉 Felicidades, el **{level.name}** de **{author_name}** ha salido victorioso **{level.clears}** veces!\n"
                    f"> ID: `{level_id}`"
                )
            if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
                await push_to_engine_bot_qq({
                    "type": f"{level.clears}_clears",
                    "level_id": level_id,
                    "level_name": level.name,
                    "author": author_name,
                })
    return StageSuccessMessage(
        success="Successfully updated clears", id=level_id, type="stats"
    )


@router.post("/{level_id}/stats/muertes")
async def stats_muertes_handler(
        level_id: str,
        dal: DBAccessLayer = Depends(create_dal),
        auth_code: str = Form(),
        session: Session = Depends(verify_and_get_session)
) -> ErrorMessage | StageSuccessMessage:
    level: Level | None = await dal.get_level_by_level_id(level_id=level_id)
    if level is None:
        return ErrorMessage(
            error_type="029", message="Level not found."
        )  # No level found
    await dal.add_death_to_level(level=level)
    await dal.commit()
    if level.deaths == 100 or level.deaths == 1000:
        if ENABLE_ENGINE_BOT_WEBHOOK and ENABLE_ENGINE_BOT_COUNTER_WEBHOOK:
            author_name: str = await get_author_name_by_level(level, dal)
            await push_to_engine_bot_qq({
                "type": f"{level.deaths}_deaths",
                "level_id": level_id,
                "level_name": level.name,
                "author": author_name,
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
