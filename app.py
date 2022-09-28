import dateutil.utils
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
    return open('website/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read())


@app.route('/user/login', methods=['POST'])
async def user_login_handler():
    data = parse_data(request)
    tokens_auth_code_match = {Tokens.PC_CN: data['alias'] + '|PC|CN', Tokens.PC_ES: data['alias'] + '|PC|ES',
                              Tokens.PC_EN: data['alias'] + '|PC|EN', Tokens.Mobile_CN: data['alias'] + '|MB|CN',
                              Tokens.Mobile_ES: data['alias'] + '|MB|ES', Tokens.Mobile_EN: data['alias'] + '|MB|EN'}
    try:
        auth_code = tokens_auth_code_match[data['token']]
        auth_data = parse_auth_code(auth_code)
    except KeyError as e:
        return jsonify({'error_type': '005', 'message': 'Illegal client.'})
    if 'SMMWEMB' in data['token']:
        mobile = True
    else:
        mobile = False
    try:
        account = db.Account.get(db.Account.username == data['alias'])
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
        return jsonify(
            {'type': 'id',
             'result':
                 level_db_to_dict(level_data=level, locale=auth_data.locale, generate_url_function=storage.generate_url,
                                  mobile=mobile)})
    except Exception as e:
        print(e)
        return jsonify({'error_type': '028', 'message': auth_data.locale_item.LEVEL_NOT_FOUND + str(e)})


@app.route('/stages/detailed_search', methods=['POST'])
async def stages_detailed_search_handler():
    print('Loading course world...')
    data = parse_data(request)
    print(data)
    auth_data = parse_auth_code(data['auth_code'])

    results = []
    levels = db.Level.select()

    # Filter and search

    if 'featured' in data:
        if data['featured'] == 'promising':
            levels = levels.where(db.Level.featured == True)  # "promising"
            print("Searching promising levels")
        else:
            if data['sort'] == 'popular':
                levels = levels.order_by(db.Level.likes.desc())  # likes
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
        levels = levels.where((db.Level.date.day - dateutil.utils.today().day) <= days)
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
            results.append(
                level_db_to_dict(level_data=level, locale=auth_data.locale, generate_url_function=storage.generate_url,
                                 mobile=mobile))
        except Exception as e:
            print(e)
    if len(results) == 0:
        return jsonify({'error_type': '029', 'message': auth_data.locale_item.LEVEL_NOT_FOUND})  # No level found
    else:
        return jsonify(
            {'type': 'detailed_search', 'num_rows': str(num_rows), 'rows_perpage': str(rows_perpage),
             'pages': str(pages), 'result': results})


@app.route('/stage/<level_id>/switch/promising', methods=['POST'])
async def switch_promising_handler(level_id):
    level = db.Level.get(db.Level.level_id == level_id)
    level.featured = True
    level.save()
    return jsonify({'success': 'success', 'id': level_id, 'type': 'stage'})


@app.route('/stage/upload', methods=['POST'])
async def stages_upload_handler():
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])
    account = db.Account.get(db.Account.username == auth_data.username)
    if account.uploads == UPLOAD_LIMIT:
        return jsonify(
            {'error_type': '025', 'message': auth_data.locale_item.UPLOAD_LIMIT_REACHED + f"({UPLOAD_LIMIT})"})
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
    except Exception as e:
        print('md5: Not duplicated')
        not_duplicated = True
    if not not_duplicated:
        print('md5: duplicated, fallback to sha1')
        level_id = gen_level_id_sha1(data_swe)

    # if duplicated again then use sha256
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except Exception as e:
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
    if non_ascii:
        return jsonify({'success': auth_data.locale_item.UPLOAD_COMPLETE_NON_ASCII, 'id': level_id, 'type': 'upload'})
    else:
        return jsonify({'success': auth_data.locale_item.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'})


# These are APIs exclusive to Engine Tribe
# Since in Engine Kingdom, the game backend and Engine-bot are integrated, so you can directly register in Engine-bot
# In Engine Tribe, they are separated, so need to add these APIs
@app.route('/user/register', methods=['POST'])  # Register account
async def user_register_handler():
    data = request.get_json()  # api_key, username, password_hash, user_id
    print('User register')
    print(data)
    if data['api_key'] != API_KEY:
        return jsonify({'error_type': '004', 'message': '引擎 bot 设置中填写的 API Key 无效。'})
        # Bot currently only supports Chinese, so it only returns Chinese
    try:
        db.add_user(username=data['username'], user_id=data['user_id'], password_hash=data['password_hash'])
        return jsonify(
            {'success': '🎉 注册成功，现在可以使用 ' + data['username'] + ' 在游戏中登录了。', 'type': 'register'})
    except Exception as e:
        return jsonify({'error_type': '255', 'message': str(e)})


@app.route('/user/update_permission', methods=['POST'])  # Update permission
async def user_set_permission_handler():
    data = request.get_json()  # username, permission, value
    print('Update permission')
    print(data)
    user = db.Account.get(db.Account.username == data['username'])
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
    return jsonify({'success': '权限已经更新', 'type': 'update'})


if __name__ == '__main__':
    db = SMMWEDatabase()
    # auto create table
    db.Level.create_table()
    db.Account.create_table()
    if STORAGE_ADAPTER == 'onedrive-cf':
        storage = StorageAdapterOneDriveCF(url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED)
    app.run(host=HOST, port=PORT, debug=FLASK_DEBUG_MODE)
