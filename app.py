import datetime

import discord
from flask import Flask, request, jsonify

from config import *
from smmwe_lib import *
from locales import *
from database import SMMWEDatabase
from storage_adapter import *

from math import ceil

app = Flask(__name__)


@app.route('/', methods=['GET'])
async def readme_handler():
    return open('pages/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read())


@app.route('/user/login', methods=['POST'])
async def user_login_handler():
    data = parse_data(request)
    tokens_auth_code_match = {Tokens.PC_CN: data['alias'] + '|PC|CN', Tokens.PC_ES: data['alias'] + '|PC|ES',
                              Tokens.PC_EN: data['alias'] + '|PC|EN', Tokens.Mobile_CN: data['alias'] + '|MB|CN',
                              Tokens.Mobile_ES: data['alias'] + '|MB|ES', Tokens.Mobile_EN: data['alias'] + '|MB|EN'}
    try:
        auth_code = tokens_auth_code_match[data['token']]
        auth_data = parse_auth_code(auth_code)
    except KeyError:
        return jsonify({'error_type': '005', 'message': 'Illegal client.'})
    if 'SMMWEMB' in data['token']:
        mobile = True
    else:
        mobile = False
    try:
        account = db.User.get(db.User.username == data['alias'])
    except Exception as e:
        return jsonify({'error_type': '006', 'message': auth_data.locale_item.ACCOUNT_NOT_FOUND})
    if not account.is_valid:
        return jsonify({'error_type': '011', 'message': auth_data.locale_item.ACCOUNT_IS_NOT_VALID})
    if account.is_banned:
        return jsonify({'error_type': '005', 'message': auth_data.locale_item.ACCOUNT_BANNED})
    if account.password_hash != calculate_password_hash(data['password']):
        return jsonify({'error_type': '007', 'message': auth_data.locale_item.ACCOUNT_ERROR_PASSWORD})
    login_user_profile = {'username': data['alias'], 'admin': account.is_admin, 'mod': account.is_mod,
                          'booster': account.is_booster, 'goomba': True, 'alias': data['alias'], 'id': account.user_id,
                          'uploads': str(account.uploads), 'mobile': mobile, 'auth_code': auth_code}
    return jsonify(login_user_profile)


@app.route('/stage/<level_id>', methods=['POST'])
async def stage_id_search_handler(level_id):
    print('Search course ' + level_id + ' ...')
    data = parse_data(request)
    print(data)
    auth_data = parse_auth_code(data['auth_code'])
    try:
        if auth_data.platform == 'MB':
            mobile = True  # Mobile fixes
        else:
            mobile = False
        level = db.Level.get(db.Level.level_id == level_id)

        # get like type from database
        try:
            stat = db.Stats.get(db.Stats.level_id == level.level_id)  # get like data
            if auth_data.username + ',' in stat.likes_users:
                like_type = '0'  # like
            elif auth_data.username + ',' in stat.dislikes_users:
                like_type = '1'  # dislike
            else:
                like_type = '0'
        except Exception as e1:
            like_type = '2'

        return jsonify(
            {'type': 'id',
             'result':
                 level_db_to_dict(level_data=level, locale=auth_data.locale, generate_url_function=storage.generate_url,
                                  mobile=mobile, like_type=like_type)})
    except Exception as e:
        print(e)
        return jsonify({'error_type': '028', 'message': auth_data.locale_item.LEVEL_NOT_FOUND + str(e)})


@app.route('/stages/detailed_search', methods=['POST'])
async def stages_detailed_search_handler():
    print('Loading course world...')
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])

    results = []
    levels = db.Level.select()

    # Filter and search

    if 'featured' in data:
        if data['featured'] == 'promising':
            levels = levels.where(db.Level.featured == True)  # "promising"
            levels = levels.order_by(db.Level.id.desc())  # latest levels
            print("Searching featured levels")
        elif data['sort'] == 'popular':
            levels = levels.order_by(db.Level.likes.desc())  # likes
            print("Searching popular levels")
    else:
        levels = levels.order_by(db.Level.id.desc())  # latest levels

    if auth_data.platform == 'MB':
        mobile = True  # Mobile fixes
    else:
        mobile = False

    if 'page' in data:
        page = int(data['page'])
    else:
        page = 1

    # detailed search

    if 'title' in data:
        levels = levels.where(db.Level.name.contains(data['title']))
    if 'author' in data:
        levels = levels.where(db.Level.author == data['author'])
    if 'aparience' in data:
        levels = levels.where(db.Level.style == data['aparience'])
    if 'entorno' in data:
        levels = levels.where(db.Level.environment == data['entorno'])
    if 'last' in data:
        days = int(data['last'].strip('d'))
        levels = levels.where((datetime.date.today().day - db.Level.date.day) <= days)
    if 'sort' in data:
        if data['sort'] == 'antiguos':
            levels = levels.order_by(db.Level.id.asc())

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
            # get like type from database
            try:
                stat = db.Stats.get(db.Stats.level_id == level.level_id)  # get like data
                if auth_data.username + ',' in stat.likes_users:
                    like_type = '0'  # like
                elif auth_data.username + ',' in stat.dislikes_users:
                    like_type = '1'  # dislike
                else:
                    like_type = '2'  # none
            except Exception as e1:
                like_type = '2'

            results.append(
                level_db_to_dict(level_data=level, locale=auth_data.locale, generate_url_function=storage.generate_url,
                                 mobile=mobile, like_type=like_type))
        except Exception as e:
            print(e)
    if len(results) == 0:
        return jsonify({'error_type': '029', 'message': auth_data.locale_item.LEVEL_NOT_FOUND})  # No level found
    else:
        return jsonify(
            {'type': 'detailed_search', 'num_rows': str(num_rows), 'rows_perpage': str(rows_perpage),
             'pages': str(pages), 'result': results})


@app.route('/stage/<level_id>/delete', methods=['POST'])
async def stage_delete_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    print(level_id + ' deleted')
    if ENABLE_DISCORD_WEBHOOK:
        webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
        message = '🗑️ **' + level.author + '** borró el nivel: **' + level.name + '**\n'
        message += 'ID: `' + level_id + '`'
        webhook.send(message, username='Engine Bot',
                     avatar_url='https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine'
                                '-bot.png')
    if ENABLE_ENGINE_BOT_WEBHOOK:
        for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
            requests.post(url=webhook_url,
                          json={'type': 'new_deleted', 'level_id': level_id, 'level_name': level.name,
                                'author': level.author})  # Send new deleted info to Engine-bot
    db.Level.delete().where(db.Level.level_id == level_id).execute()
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stage'})


@app.route('/stage/<level_id>/switch/promising', methods=['POST'])
async def switch_promising_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    if not level.featured:
        level.featured = True
        print(level_id + ' added to featured')
        for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
            requests.post(url=webhook_url,
                          json={'type': 'new_featured', 'level_id': level_id, 'level_name': level.name,
                                'author': level.author})  # Send new featured info to Engine-bot
    else:
        print(level_id + ' removed from featured')
        level.featured = False
    level.save()
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stage'})


@app.route('/stage/<level_id>/stats/intentos', methods=['POST'])
async def stats_intentos_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    level.plays += 1
    level.save()
    if ENABLE_DISCORD_WEBHOOK:
        if level.clears == 100 or level.clears == 1000:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = '🎉 Felicidades, el **' + level.name + '** de **' + level.author + '** ha sido reproducido **' \
                      + level.plays + '** veces!\n'
            message += 'ID: `' + level_id + '`'
            webhook.send(message, username='Engine Bot',
                         avatar_url='https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine'
                                    '-bot.png')
    if ENABLE_ENGINE_BOT_WEBHOOK:
        if level.plays == 100:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '100_plays', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})
        if level.plays == 1000:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '1000_plays', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send plays info to Engine-bot
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stats'})


@app.route('/stage/<level_id>/stats/victorias', methods=['POST'])
async def stats_victorias_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    level.clears += 1
    level.save()
    if ENABLE_DISCORD_WEBHOOK:
        if level.clears == 100 or level.clears == 1000:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = '🎉 Felicidades, el **' + leve.name + '** de **' + level.author + '** ha salido victorioso **' +\
                      level.clears + '** veces!\n'
            message += 'ID: `' + level_id + '`'
            webhook.send(message, username='Engine Bot',
                         avatar_url='https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine'
                                    '-bot.png')
    if ENABLE_ENGINE_BOT_WEBHOOK:
        if level.clears == 100:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '100_clears', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})
        if level.clears == 1000:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '1000_clears', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send clears info to Engine-bot
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stats'})


@app.route('/stage/<level_id>/stats/muertes', methods=['POST'])
async def stats_muertes_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    level.deaths += 1
    level.save()
    if ENABLE_ENGINE_BOT_WEBHOOK:
        if level.deaths == 100:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '100_deaths', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})
        if level.deaths == 1000:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '1000_deaths', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send deaths info to Engine-bot
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stats'})


@app.route('/stage/<level_id>/stats/likes', methods=['POST'])
async def stats_likes_handler(level_id):
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except:
        stat = db.Stats(level_id=level_id, likes_users='', dislikes_users='')
    stat.likes_users += username + ','
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.likes += 1
    level.save()
    if ENABLE_DISCORD_WEBHOOK:
        if level.likes == 10 or level.likes == 100 or level.likes == 1000:
            webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
            message = '🎉 Felicidades, el **' + level.name + '** de **' + level.author + '** tiene **' + \
                      level.likes + '** me gusta!\n'
            message += 'ID: `' + level_id + '`'
            webhook.send(message, username='Engine Bot',
                         avatar_url='https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine'
                                    '-bot.png')
    if ENABLE_ENGINE_BOT_WEBHOOK:
        if level.likes == 10:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '10_likes', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})
        if level.likes == 100:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '100_likes', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})
        if level.likes == 1000:
            for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
                requests.post(url=webhook_url,
                              json={'type': '1000_likes', 'level_id': level_id, 'level_name': level.name,
                                    'author': level.author})  # Send likes info to Engine-bot
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stats'})


@app.route('/stage/<level_id>/stats/dislikes', methods=['POST'])
async def stats_dislikes_handler(level_id):
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])
    username = auth_data.username
    try:
        stat = db.Stats.get(db.Stats.level_id == level_id)
    except:
        stat = db.Stats(level_id=level_id, likes_users='', dislikes_users='')
    stat.dislikes_users += username + ','
    stat.save()
    level = db.Level.get(db.Level.level_id == level_id)
    level.dislikes += 1
    level.save()
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stats'})


@app.route('/stage/upload', methods=['POST'])
async def stages_upload_handler():
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])
    account = db.User.get(db.User.username == auth_data.username)
    if account.is_booster:
        upload_limit = UPLOAD_LIMIT + 10
    elif account.is_mod or account.is_admin:
        upload_limit = 999
    else:
        upload_limit = UPLOAD_LIMIT
    if account.uploads >= upload_limit:
        return jsonify(
            {'error_type': '025', 'message': auth_data.locale_item.UPLOAD_LIMIT_REACHED + f"({upload_limit})"})
    data_swe = data['swe']

    print('Uploading level ' + data['name'])

    # check non-ASCII
    non_ascii = False
    print((re.sub(r'[ -~]', '', data['name'])))
    if (re.sub(r'[ -~]', '', data['name'])) != "":
        non_ascii = True

    # generate level id
    level_id = gen_level_id_md5(data_swe)

    # check duplicated level ID
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except:
        print('md5: Not duplicated')
        not_duplicated = True
    if not not_duplicated:
        print('md5: duplicated, fallback to sha1')
        level_id = gen_level_id_sha1(data_swe)

    # if duplicated again then use sha256
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except:
        print('sha1: Not duplicated')
        not_duplicated = True
    if not not_duplicated:
        print('sha1: duplicated, fallback to sha256')
        level_id = gen_level_id_sha256(data_swe)

    print("Uploading level to storage backend...")
    if len(data_swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return jsonify({'error_type': '025', 'message': auth_data.locale_item.FILE_TOO_LARGE})
    try:
        storage.upload_file(level_name=data['name'], level_data=data_swe,
                            level_id=level_id)  # Upload to storage backend
    except ConnectionError as e:
        return jsonify({'error_type': '009', 'message': auth_data.locale_item.UPLOAD_CONNECT_ERROR})

    db.add_level(data['name'], data['aparience'], data['entorno'], data['tags'], auth_data.username, level_id,
                 non_ascii)
    account.uploads += 1
    account.save()
    if ENABLE_DISCORD_WEBHOOK:
        webhook = discord.SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
        message = '📤 **' + auth_data.username + '** subió un nuevo nivel: **' + data['name'] + '**\n'
        message += 'ID: `' + level_id + '`'
        webhook.send(message, username='Engine Bot',
                     avatar_url='https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine'
                                '-bot.png')
    if ENABLE_ENGINE_BOT_WEBHOOK:
        for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
            requests.post(url=webhook_url,
                          json={'type': 'new_arrival', 'level_id': level_id, 'level_name': data['name'],
                                'author': auth_data.username})  # Send new level info to Engine-bot
    return jsonify({'success': auth_data.locale_item.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'})


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine Bot are integrated, so you can directly register in Engine Bot
# In Engine Tribe, they are separated, so need to use these APIs
@app.route('/user/register', methods=['POST'])  # Register account
async def user_register_handler():
    data = request.get_json()  # api_key, username, password_hash, user_id
    print('User register')
    print(data)
    if data['api_key'] != API_KEY:
        return jsonify({'error_type': '004', 'message': 'Invalid API key.', 'api_key': data['api_key']})
    user_exist = True
    try:
        db.User.get(db.User.user_id == data['user_id'])
    except:
        user_exist = False
    if user_exist:
        return jsonify({'error_type': '035', 'message': 'User ID already exists.', 'user_id': data['user_id']})
    user_exist = True
    try:
        db.User.get(db.User.username == data['username'])
    except:
        user_exist = False
    if user_exist:
        return jsonify({'error_type': '036', 'message': 'Username already exists.', 'username': data['username']})
    try:
        db.add_user(username=data['username'], user_id=data['user_id'], password_hash=data['password_hash'])
        return jsonify(
            {'success': 'Registration success.', 'username': data['username'], 'user_id': data['user_id'],
             'type': 'register'})
    except Exception as e:
        return jsonify({'error_type': '255', 'message': str(e)})


@app.route('/user/update_permission', methods=['POST'])  # Update permission
async def user_set_permission_handler():
    data = request.get_json()  # username/user_id, permission, value
    print('Update permission')
    print(data)
    try:
        if 'username' in data:
            user = db.User.get(db.User.username == data['username'])
        elif 'user_id' in data:
            user = db.User.get(db.User.user_id == data['user_id'])
        else:
            return jsonify({'error_type': '255', 'message': 'API error.'})
    except Exception as e:
        return jsonify({'error_type': '006', 'message': 'User not found.'})
    if data['permission'] == 'mod':
        user.is_mod = data['value']
    elif data['permission'] == 'admin':
        user.is_admin = data['value']
    elif data['permission'] == 'booster':
        user.is_booster = data['value']
    elif data['permission'] == 'valid':
        user.is_valid = data['value']
    elif data['permission'] == 'banned':
        user.is_banned = data['value']
    user.save()
    return jsonify({'success': 'Update success', 'type': 'update', 'user_id': user.user_id, 'username': user.username})


@app.route('/user/info', methods=['POST'])  # get user info
async def user_info_handler():
    data = request.get_json()  # username/user_id
    try:
        if 'username' in data:
            user = db.User.get(db.User.username == data['username'])
        elif 'user_id' in data:
            user = db.User.get(db.User.user_id == data['user_id'])
        else:
            return jsonify({'error_type': '255', 'message': 'API error.'})
    except Exception as e:
        return jsonify({'error_type': '006', 'message': 'User not found.'})
    return jsonify(
        {'type': 'user', 'result': {'user_id': user.user_id, 'username': user.username, 'uploads': int(user.uploads),
                                    'is_admin': user.is_admin, 'is_mod': user.is_mod, 'is_booster': user.is_booster,
                                    'is_valid': user.is_valid, 'is_banned': user.is_banned}})


if __name__ == '__main__':
    db = SMMWEDatabase()
    # auto create table
    db.Level.create_table()
    db.User.create_table()
    db.Stats.create_table()
    if STORAGE_ADAPTER == 'onedrive-cf':
        storage = StorageAdapterOneDriveCF(url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED)
    app.run(host=HOST, port=PORT, debug=FLASK_DEBUG_MODE)
