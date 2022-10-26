import datetime
from math import ceil

import discord  # Discord webhook support
import peewee
from peewee import fn
import uvicorn
from fastapi import FastAPI, Form, Header
from fastapi.responses import RedirectResponse
from typing import Union
import threading
import platform
import datetime
import requests

from config import *
from database import SMMWEDatabase
from models import *
from smmwe_lib import *
from storage_adapter import *
from dfa_filter import DFAFilter
from locales import es_ES

app = FastAPI()
db = SMMWEDatabase()
connection_count = 0
connection_per_minute = 0
start_time = datetime.datetime.now()

# auto create table
db.Level.create_table()
db.User.create_table()
db.Stats.create_table()

# Only onedrive-cf storage adapter is supported now
# ~~In fact, it should be provider not adapter, too lazy to change it~~
if STORAGE_ADAPTER == 'onedrive-cf':
    storage = StorageAdapterOneDriveCF(url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED)

if OFFENSIVE_WORDS_FILTER:
    # Load DFA filter
    dfa_filter = DFAFilter()
    for url in OFFENSIVE_WORDS_LIST:
        wordlist = requests.get(url=url).text.replace('\r', '').split('\n')
        for word in wordlist:
            if len(word) > 1 and len(word.encode('utf-8')) > 2:
                dfa_filter.add(word)
    for url in OFFENSIVE_WORDS_LIST_CN_ONLY:
        wordlist = requests.get(url=url).text.replace('\r', '').split('\n')
        for word in wordlist:
            if len(re.findall(re.compile(r'[A-Za-z]', re.S), word)) == 0:
                if len(word) > 1 and len(word.encode('utf-8')) > 2:
                    dfa_filter.add(word)


@app.get('/')
async def readme_handler():  # Redirect to Engine Tribe README
    return RedirectResponse('https://web.enginetribe.gq/index.html')


@app.post('/user/login')
async def user_login_handler(user_agent: Union[str, None] = Header(default=None), alias: str = Form(''),
                             token: str = Form(''), password: str = Form('')):  # User login
    # match auth_code to generate token
    tokens_auth_code_match = {
        Tokens.PC_CN: f'{alias}|PC|CN',
        Tokens.PC_ES: f'{alias}|PC|ES',
        Tokens.PC_EN: f'{alias}|PC|EN',
        Tokens.Mobile_CN: f'{alias}|MB|CN',
        Tokens.Mobile_ES: f'{alias}|MB|ES',
        Tokens.Mobile_EN: f'{alias}|MB|EN',
        Tokens.PC_Legacy_CN: f'{alias}|PC|CN|L',
        Tokens.PC_Legacy_ES: f'{alias}|PC|ES|L',
        Tokens.PC_Legacy_EN: f'{alias}|PC|EN|L',
        Tokens.Mobile_Legacy_CN: f'{alias}|MB|CN|L',
        Tokens.Mobile_Legacy_ES: f'{alias}|MB|ES|L',
        Tokens.Mobile_Legacy_EN: f'{alias}|MB|EN|L'
    }

    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')

    password = password.encode('latin1').decode('utf-8')
    # Fix for Starlette
    # https://github.com/encode/starlette/issues/425

    # match the token
    try:
        auth_code = tokens_auth_code_match[token]
        auth_data = parse_auth_code(auth_code)
    except KeyError:
        return ErrorMessage(error_type='005', message='Illegal client.')

    if 'SMMWEMB' in token:
        mobile = True
    else:
        mobile = False

    try:
        account = db.User.get(db.User.username == alias)
    except peewee.DoesNotExist:
        return ErrorMessage(error_type='006', message=auth_data.locale_item.ACCOUNT_NOT_FOUND)
    if not account.is_valid:
        return ErrorMessage(error_type='011', message=auth_data.locale_item.ACCOUNT_IS_NOT_VALID)
    if account.is_banned:
        return ErrorMessage(error_type='005', message=auth_data.locale_item.ACCOUNT_BANNED)
    if account.password_hash != calculate_password_hash(password):
        return ErrorMessage(error_type='007', message=auth_data.locale_item.ACCOUNT_ERROR_PASSWORD)
    if '|L' in auth_code:
        login_user_profile = {'goomba': True, 'alias': alias, 'id': account.user_id, 'auth_code': auth_code,
                              'ip': '127.0.0.1'}
    else:
        login_user_profile = {'username': alias, 'admin': account.is_admin, 'mod': account.is_mod,
                              'booster': account.is_booster, 'goomba': True, 'alias': alias, 'id': account.user_id,
                              'uploads': str(account.uploads), 'mobile': mobile, 'auth_code': auth_code}
    return login_user_profile


@app.post('/stage/upload')
async def stages_upload_handler(user_agent: Union[str, None] = Header(default=None), auth_code: str = Form(),
                                swe: str = Form(), name: str = Form(), aparience: str = Form(),
                                entorno: str = Form(), tags: str = Form()):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')

    auth_data = parse_auth_code(auth_code)
    account = db.User.get(db.User.username == auth_data.username)

    if account.is_booster:
        upload_limit = UPLOAD_LIMIT + BOOSTERS_EXTRA_LIMIT
    elif account.is_mod or account.is_admin:
        upload_limit = 999  # Almost infinite
    else:
        upload_limit = UPLOAD_LIMIT
    if account.uploads >= upload_limit:
        return ErrorMessage(error_type='025', message=auth_data.locale_item.UPLOAD_LIMIT_REACHED + f"({upload_limit})")

    name = name.encode('latin1').decode('utf-8')
    tags = tags.encode('latin1').decode('utf-8')
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    print('Uploading level ' + name)

    if OFFENSIVE_WORDS_FILTER:  # Apply filter
        name_filtered = dfa_filter.filter(name)
        if name_filtered != name.lower():
            name = name_filtered

    # check non-Latin
    non_latin = False
    if (re.sub(u'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]', u'', name)) != name:
        non_latin = True

    # check testing client
    if auth_data.testing_client:
        testing_client = True
    else:
        testing_client = False

    # generate level id
    swe_to_generate = strip_level(swe)
    level_id = gen_level_id_md5(swe_to_generate)

    # check duplicated level ID
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except peewee.DoesNotExist:
        print('md5: Not duplicated')
        not_duplicated = True
    if not not_duplicated:
        print('md5: duplicated, fallback to sha1')
        level_id = gen_level_id_sha1(swe_to_generate)

    if not not_duplicated:
        # if duplicated again then use sha256
        try:
            db.Level.get(db.Level.level_id == level_id)
        except peewee.DoesNotExist:
            print('sha1: Not duplicated')
            not_duplicated = True
        if not not_duplicated:
            print('sha1: duplicated, fallback to sha256')
            level_id = gen_level_id_sha256(swe_to_generate)

    if not not_duplicated:
        # if sha256 duplicated again then return error
        try:
            db.Level.get(db.Level.level_id == level_id)
        except peewee.DoesNotExist:
            print('sha256: Not duplicated')
            not_duplicated = True
        if not not_duplicated:
            return ErrorMessage(error_type='009', message=auth_data.locale_item.LEVEL_ID_REPEAT)

    if len(swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return ErrorMessage(error_type='025', message=auth_data.locale_item.FILE_TOO_LARGE)
    try:
        storage.upload_file(level_data=swe, level_id=level_id)  # Upload to storage backend
    except ConnectionError:
        return ErrorMessage(error_type='009', message=auth_data.locale_item.UPLOAD_CONNECT_ERROR)

    db.add_level(name, aparience, entorno, tags, auth_data.username, level_id, non_latin, testing_client)
    account.uploads += 1
    account.save()
    if ENABLE_DISCORD_WEBHOOK:
        webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
        message = f'📤 **{auth_data.username}** subió un nuevo nivel: **{name}**\n'
        message += f'ID: `{level_id}`  Tags: `{tags.split(",")[0].strip()}, {tags.split(",")[1].strip()}`\n'
        message += f'Descargar: {storage.generate_download_url(level_id=level_id)}'
        webhook.send(message, username='Engine Bot', avatar_url=DISCORD_AVATAR_URL)
    if ENABLE_ENGINE_BOT_WEBHOOK:
        for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
            requests.post(url=webhook_url,
                          json={'type': 'new_arrival', 'level_id': level_id, 'level_name': name,
                                'author': auth_data.username})  # Send new level info to Engine-bot
    return {'success': auth_data.locale_item.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'}


@app.post('/stages/detailed_search')
async def stages_detailed_search_handler(user_agent: Union[str, None] = Header(default=None),
                                         auth_code: str = Form('EngineBot|PC|CN'), featured: Optional[str] = Form(None),
                                         page: Optional[str] = Form('1'), title: Optional[str] = Form(None),
                                         author: Optional[str] = Form(None), aparience: Optional[str] = Form(None),
                                         entorno: Optional[str] = Form(None), last: Optional[str] = Form(None),
                                         sort: Optional[str] = Form(None), liked: Optional[str] = Form(None),
                                         disliked: Optional[str] = Form(None), historial: Optional[str] = Form(None),
                                         dificultad: Optional[str] = Form(None)):  # Detailed search (level list)

    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')

    if title:
        title = title.encode('latin1').decode('utf-8')
    # Fixes for Starlette
    # https://github.com/encode/starlette/issues/425

    auth_data = parse_auth_code(auth_code)

    results = []
    levels = db.Level.select()

    # Filter and search

    if featured:
        if featured == 'promising':
            levels = levels.where(db.Level.featured == True)  # featured levels
            levels = levels.order_by(db.Level.id.desc())  # latest levels
        elif featured == 'popular':
            levels = levels.order_by((db.Level.likes - db.Level.dislikes).desc())  # likes
    else:
        levels = levels.order_by(db.Level.id.desc())  # latest levels

    # avoid non-testing client error
    if not auth_data.testing_client:
        levels = levels.where(db.Level.testing_client == False)

    if auth_data.platform == 'MB':
        mobile = True  # Mobile fixes
    else:
        mobile = False

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
        days = int(last.strip('d'))
        levels = levels.where(
            db.Level.date.between(datetime.date.today() + datetime.timedelta(days=-days), datetime.date.today()))
    if sort:
        if sort == 'antiguos':
            levels = levels.order_by(db.Level.id.asc())
    if liked:
        stats = db.Stats.select().where(db.Stats.likes_users.contains(auth_data.username))
        # Engine Tribe stores the username of the liker instead of the ID, so the username in auth_code is used here
        level_ids = []
        for stat in stats:
            level_ids.append(stat.level_id)
        levels = levels.where(db.Level.level_id.in_(level_ids))
    elif disliked:
        stats = db.Stats.select().where(db.Stats.dislikes_users.contains(auth_data.username))
        level_ids = []
        for stat in stats:
            level_ids.append(stat.level_id)
        levels = levels.where(db.Level.level_id.in_(level_ids))
    if dificultad:
        levels = levels.where(db.Level.deaths != 0)
        if dificultad == '0':
            levels = levels.where((db.Level.clears / db.Level.deaths).between(0.8, 10.0))
        elif dificultad == '1':
            levels = levels.where((db.Level.clears / db.Level.deaths).between(0.5, 0.8))
        elif dificultad == '2':
            levels = levels.where((db.Level.clears / db.Level.deaths).between(0.3, 0.5))
        else:
            levels = levels.where((db.Level.clears / db.Level.deaths).between(0.0, 0.3))

    if historial:
        return ErrorMessage(error_type='255', message=auth_data.locale_item.NOT_IMPLEMENTED)

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
            like_type = db.get_like_type(level_id=level.level_id, username=auth_data.username)
            results.append(
                level_db_to_dict(level_data=level, locale=auth_data.locale,
                                 generate_url_function=storage.generate_url,
                                 mobile=mobile, like_type=like_type))
        except Exception as e:
            print(e)
    if len(results) == 0:
        return ErrorMessage(error_type='029', message=auth_data.locale_item.LEVEL_NOT_FOUND)  # No level found
    else:
        return {'type': 'detailed_search', 'num_rows': str(num_rows), 'rows_perpage': str(rows_perpage),
                'pages': str(pages), 'result': results}


@app.post('/stage/random')
async def stage_id_random_handler(user_agent: Union[str, None] = Header(default=None),
                                  auth_code: str = Form('EngineBot|PC|CN')):  # Random level
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    auth_data = parse_auth_code(auth_code)
    if auth_data.platform == 'MB':
        mobile = True  # Mobile fixes
    else:
        mobile = False
    if db.db_type == 'mysql':
        level = db.Level.select().order_by(peewee.fn.Rand()).limit(1)[0]
    else:
        level = db.Level.select().order_by(peewee.fn.Random()).limit(1)[0]  # postgresql and sqlite
    like_type = db.get_like_type(level_id=level.level_id, username=auth_data.username)
    return {'type': 'id', 'result': level_db_to_dict(level_data=level, locale=auth_data.locale,
                                                     generate_url_function=storage.generate_url, mobile=mobile,
                                                     like_type=like_type)}


@app.post('/stage/{level_id}')
async def stage_id_search_handler(level_id: str, user_agent: Union[str, None] = Header(default=None),
                                  auth_code: str = Form('EngineBot|PC|CN')):  # Level ID search
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    auth_data = parse_auth_code(auth_code)
    try:
        if auth_data.platform == 'MB':
            mobile = True  # Mobile fixes
        else:
            mobile = False
        level = db.Level.get(db.Level.level_id == level_id)
        like_type = db.get_like_type(level_id=level.level_id, username=auth_data.username)
        return {'type': 'id', 'result': level_db_to_dict(level_data=level, locale=auth_data.locale,
                                                         generate_url_function=storage.generate_url, mobile=mobile,
                                                         like_type=like_type)}
    except Exception as ex:
        print(ex)
        return ErrorMessage(error_type='029', message=auth_data.locale_item.LEVEL_NOT_FOUND)  # No level found


@app.post('/stage/{level_id}/delete')
async def stage_delete_handler(level_id: str):  # Delete level
    global connection_count
    connection_count += 1
    level = db.Level.get(db.Level.level_id == level_id)
    db.Level.delete().where(db.Level.level_id == level_id).execute()
    user = db.User.get(db.User.username == level.author)
    user.uploads -= 1
    user.save()
    return {'success': 'success', 'id': level_id, 'type': 'stage'}


@app.post('/stage/{level_id}/switch/promising')
async def switch_promising_handler(level_id: str, user_agent: Union[str, None] = Header(default=None)):
    # Switch featured (promising) level
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    level = db.Level.get(db.Level.level_id == level_id)
    if not level.featured:
        level.featured = True
        level.save()
        print(level_id + ' added to featured')
        if ENABLE_DISCORD_WEBHOOK:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = f'🌟 El **{level.name}** por **{level.author}** se agrega a niveles prometedores! \n '
            message += f'ID: `{level_id}`'
            webhook.send(message, username='Engine Bot', avatar_url=DISCORD_AVATAR_URL)
        if ENABLE_ENGINE_BOT_WEBHOOK:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': 'new_featured', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send new featured info to Engine-bot
    else:
        level.featured = False
        level.save()
        print(level_id + ' removed from featured')
    return {'success': 'success', 'id': level_id, 'type': 'stage'}


@app.post('/stage/{level_id}/stats/intentos')
async def stats_intentos_handler(level_id: str, user_agent: Union[str, None] = Header(default=None)):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    level = db.Level.get(db.Level.level_id == level_id)
    level.plays += 1
    level.save()
    if level.plays == 100 or level.plays == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = f'🎉 Felicidades, el **{level.name}** de **{level.author}** ha sido reproducido **{level.plays}** veces!\n'
            message += f'ID: `{level_id}`'
            webhook.send(message, username='Engine Bot', avatar_url=DISCORD_AVATAR_URL)
        if ENABLE_ENGINE_BOT_WEBHOOK:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': f'{level.plays}_plays', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send plays info to Engine-bot
    return {'success': 'success', 'id': level_id, 'type': 'stats'}


@app.post('/stage/{level_id}/stats/victorias')
async def stats_victorias_handler(level_id: str, tiempo: str = Form(), auth_code: str = Form('EngineBot|PC|CN'),
                                  user_agent: Union[str, None] = Header(default=None)):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    level = db.Level.get(db.Level.level_id == level_id)
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
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = f'🎉 Felicidades, el **{level.name}** de **{level.author}** ha salido victorioso **{level.clears}** veces!\n'
            message += f'ID: `{level_id}`'
            webhook.send(message, username='Engine Bot', avatar_url=DISCORD_AVATAR_URL)
        if ENABLE_ENGINE_BOT_WEBHOOK:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': f'{level.clears}_clears', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send clears info to Engine-bot
    return {'success': 'success', 'id': level_id, 'type': 'stats'}


@app.post('/stage/{level_id}/stats/muertes')
async def stats_muertes_handler(level_id: str, user_agent: Union[str, None] = Header(default=None)):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    level = db.Level.get(db.Level.level_id == level_id)
    level.deaths += 1
    level.save()
    if level.deaths == 100 or level.deaths == 1000:
        if ENABLE_ENGINE_BOT_WEBHOOK:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': f'{level.deaths}_deaths', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send deaths info to Engine-bot
    return {'success': 'success', 'id': level_id, 'type': 'stats'}


@app.post('/stage/{level_id}/stats/likes')
async def stats_likes_handler(level_id: str, auth_code: str = Form(),
                              user_agent: Union[str, None] = Header(default=None)):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except peewee.DoesNotExist:
        stat = db.Stats(level_id=level_id, likes_users='', dislikes_users='')
    stat.likes_users += username + ','
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.likes += 1
    level.save()
    if level.likes == 100 or level.likes == 1000:
        if ENABLE_DISCORD_WEBHOOK:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = f'🎉 Felicidades, el **{level.name}** de **{level.author}** tiene **{level.likes}** me gusta!\n'
            message += f'ID: `{level_id}`'
            webhook.send(message, username='Engine Bot', avatar_url=DISCORD_AVATAR_URL)
        if ENABLE_ENGINE_BOT_WEBHOOK:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': f'{level.likes}_likes', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send likes info to Engine-bot
    return {'success': 'success', 'id': level_id, 'type': 'stats'}


@app.post('/stage/{level_id}/stats/dislikes')
async def stats_dislikes_handler(level_id: str, auth_code: str = Form(),
                                 user_agent: Union[str, None] = Header(default=None)):
    global connection_count
    connection_count += 1
    if not is_valid_user_agent(user_agent):
        return ErrorMessage(error_type='005', message='Illegal client.')
    auth_data = parse_auth_code(auth_code)
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except peewee.DoesNotExist:
        stat = db.Stats(level_id=level_id, likes_users='', dislikes_users='')
    stat.dislikes_users += username + ','
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.dislikes += 1
    level.save()
    return {'success': 'success', 'id': level_id, 'type': 'stats'}


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs
@app.post('/user/register')  # Register account
async def user_register_handler(request: RegisterRequestBody):
    global connection_count
    connection_count += 1
    if request.api_key != API_KEY:
        return {'error_type': '004', 'message': 'Invalid API key.', 'api_key': request.api_key}
    user_exist = True
    try:
        db.User.get(db.User.user_id == request.user_id)
    except:
        user_exist = False
    if user_exist:
        return {'error_type': '035', 'message': 'User ID already exists.', 'user_id': request.user_id}
    user_exist = True
    try:
        db.User.get(db.User.username == request.username)
    except:
        user_exist = False
    if user_exist:
        return {'error_type': '036', 'message': 'Username already exists.', 'username': request.username}
    try:
        db.add_user(username=request.username, user_id=request.user_id, password_hash=request.password_hash)
        return {'success': 'Registration success.', 'username': request.username, 'user_id': request.user_id,
                'type': 'register'}
    except Exception as e:
        return ErrorMessage(error_type='255', message=str(e))


@app.post('/user/update_permission')  # Update permission
async def user_set_permission_handler(request: UpdatePermissionRequestBody):
    # username/user_id, permission, value, api_key
    global connection_count
    connection_count += 1
    if request.api_key != API_KEY:
        return {'error_type': '004', 'message': 'Invalid API key.', 'api_key': request.api_key}
    try:
        if request.username:
            user = db.User.get(db.User.username == request.username)
        elif request.user_id:
            user = db.User.get(db.User.user_id == request.user_id)
        else:
            return ErrorMessage(error_type='255', message='API error.')
    except peewee.DoesNotExist:
        return ErrorMessage(error_type='006', message='User not found.')
    if request.permission == 'mod':
        user.is_mod = request.value
    elif request.permission == 'admin':
        user.is_admin = request.value
    elif request.permission == 'booster':
        user.is_booster = request.value
    elif request.permission == 'valid':
        user.is_valid = request.value
    elif request.permission == 'banned':
        user.is_banned = request.value
    else:
        return ErrorMessage(error_type='255', message='Permission does not exist.')
    user.save()
    return {'success': 'Update success', 'type': 'update', 'user_id': user.user_id, 'username': user.username,
            'permission': request.permission, 'value': request.value}


@app.post('/user/update_password')  # Update password
async def user_update_password_handler(request: UpdatePasswordRequestBody):
    # username, password_hash, api_key
    global connection_count
    connection_count += 1
    if request.api_key != API_KEY:
        return {'error_type': '004', 'message': 'Invalid API key.', 'api_key': request.api_key}
    try:
        user = db.User.get(db.User.username == request.username)
    except peewee.DoesNotExist:
        return ErrorMessage(error_type='006', message='User not found.')
    user.password_hash = request.password_hash
    user.save()
    return {'success': 'Update success', 'type': 'update', 'username': user.username}


@app.post('/user/info')  # Get user info
async def user_info_handler(request: UserInfoRequestBody):
    global connection_count
    connection_count += 1
    try:
        if request.username:
            user = db.User.get(db.User.username == request.username)
        elif request.user_id:
            user = db.User.get(db.User.user_id == request.user_id)
        else:
            return ErrorMessage(error_type='255', message='API error.')
    except peewee.DoesNotExist:
        return ErrorMessage(error_type='006', message='User not found.')
    return {'type': 'user', 'result': {'user_id': user.user_id, 'username': user.username, 'uploads': int(user.uploads),
                                       'is_admin': user.is_admin, 'is_mod': user.is_mod, 'is_booster': user.is_booster,
                                       'is_valid': user.is_valid, 'is_banned': user.is_banned}}


# get server status
@app.get('/server_stats')
async def server_stats():
    global connection_per_minute, start_time
    return {
        'os': f'{platform.platform()}',
        'python': platform.python_version(),
        'player_count': db.User.select().count(),
        'level_count': db.Level.select().count(),
        'uptime': datetime.datetime.now() - start_time,
        'connection_per_minute': connection_per_minute
    }


# APIs for legacy client

@app.get('/stage/{level_id}/file')
async def legacy_stage_file(level_id: str):
    try:
        return {'data': requests.get(storage.generate_url(level_id)).text}
    except Exception as ex:
        print(ex)
        return ErrorMessage(error_type='029', message=es_ES.LEVEL_NOT_FOUND)  # No level found


def timer_function():
    global connection_count, connection_per_minute
    connection_per_minute = connection_count
    connection_count = 0
    threading.Timer(60, timer_function).start()


if __name__ == '__main__':
    threading.Timer(1, timer_function).start()
    uvicorn.run(app, host=HOST, port=PORT)
