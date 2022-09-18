import re

from flask import Flask, request, jsonify

from config import *
from database import SMMWEDatabase
from smmwe_lib import *
from locales import en_US, es_ES, zh_CN, convert_tags
from storage_adapter import StorageAdapterOneDriveCF

from math import ceil

app = Flask(__name__)


@app.route('/', methods=['GET'])
async def readme_handler():
    return open('website/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read())


@app.route('/user/login', methods=['POST'])
async def user_login_handler():
    data = parse_data(request)
    login_user_profile = {'username': data['alias'], 'admin': False, 'mod': False, 'booster': False, 'goomba': True,
                          'alias': data['alias'],
                          'id': '0000000000', 'uploads': '0'}
    tokens_auth_code_match = {Tokens.PC_CN: data['alias'] + '|PC|CN', Tokens.PC_ES: data['alias'] + '|PC|ES',
                              Tokens.PC_EN: data['alias'] + '|PC|EN', Tokens.Mobile_CN: data['alias'] + '|MB|CN',
                              Tokens.Mobile_ES: data['alias'] + '|MB|ES', Tokens.Mobile_EN: data['alias'] + '|MB|EN'}
    login_user_profile['auth_code'] = tokens_auth_code_match[login_user_profile['token']]
    if 'SMMWEMB' in login_user_profile['token']:
        login_user_profile['mobile'] = True
    else:
        login_user_profile['mobile'] = False
    return jsonify(login_user_profile)


@app.route('/stages/detailed_search', methods=['POST'])
async def stages_detailed_search_handler():
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])

    results = []
    levels = db.Level.select()

    try:
        if data['featured'] == 'notpromising':  # moderator recommend not implemented
            if data['sort'] == 'popular':
                levels = levels.order_by(db.Level.likes.desc())  # likes
        else:
            levels = levels.order_by(db.Level.id.desc())  # "promising"
    except KeyError as e:
        levels = levels.order_by(db.Level.id.desc())  # latest levels
    finally:
        print('Loading course world...')

    # calculate numbers
    num_rows = len(levels)
    if num_rows > ROWS_PERPAGE:
        rows_perpage = ROWS_PERPAGE + 1
        pages = ceil(num_rows / ROWS_PERPAGE)
    else:
        rows_perpage = num_rows
        pages = 1

    if 'page' in data:
        skip = (int(data['page'][0]) - 1) * ROWS_PERPAGE
    else:
        skip = 0
    for level in range(0 + skip, rows_perpage + skip - 1):
        try:
            results.append(level_class_to_dict(levels[level], locale=auth_data.locale, proxied=storage.proxied,
                                               convert_url_function=storage.convert_url))
        except Exception as e:
            print(Exception)
        finally:
            print(level)
    return jsonify(
        {'type': 'detailed_search', 'num_rows': str(num_rows), 'rows_perpage': str(rows_perpage), 'pages': str(pages),
         'result': results})


@app.route('/stage/upload', methods=['POST'])
async def stages_upload_handler():
    data = parse_data(request)
    auth_data = parse_auth_code(data['auth_code'])
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
        return jsonify({'error_type': '025', 'message': data.locale_item.FILE_TOO_LARGE})

    storage.upload_file(file_name=data['name'] + '.swe', file_data=data_swe)  # Upload to storage backend

    data['tags'] = convert_tags('ES', 'CN', data['tags'])
    data['tags'] = convert_tags('EN', 'CN', data['tags'])

    db.add_level(data['name'], data['aparience'], data['entorno'], data['tags'], auth_data.username, level_id,
                 non_ascii)
    if non_ascii:
        return jsonify({'success': data.locale_item.UPLOAD_COMPLETE_NON_ASCII, 'id': level_id, 'type': 'upload'})
    else:
        return jsonify({'success': data.locale_item.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'})


if __name__ == '__main__':
    db = SMMWEDatabase()
    db.Level.create_table()  # auto create table
    if STORAGE_ADAPTER == 'onedrive-cf':
        storage = StorageAdapterOneDriveCF(url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED)
    app.run(host=HOST, port=PORT, debug=True)
