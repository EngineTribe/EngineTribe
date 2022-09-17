import json
import re

import requests
from flask import Flask, request, jsonify
from urllib.parse import parse_qs

from config import *
from database import SMMWEDatabase
from smmwe_lib import *

from locales import *

from math import ceil

app = Flask(__name__)


@app.route('/', methods=['GET'])
async def readme_handler():
    return open('website/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read())


@app.route('/user/login', methods=['POST'])
async def user_login_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    login_user = {'username': data['alias'][0], 'admin': False, 'mod': False, 'booster': False, 'goomba': True,
                  'alias': data['alias'][0],
                  'id': '0000000000', 'uploads': '0'}
    if data['token'][0] == Tokens.PC_CN:
        login_user['mobile'] = False
        login_user['auth_code'] = data['alias'][0] + '|PC|CN'
    elif data['token'][0] == Tokens.PC_ES:
        login_user['mobile'] = False
        login_user['auth_code'] = data['alias'][0] + '|PC|ES'
    else:
        login_user['mobile'] = True
        login_user['auth_code'] = data['alias'][0] + '|Mobile'
    return jsonify(login_user)


@app.route('/stages/detailed_search', methods=['POST'])
async def stages_detailed_search_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    locale = data['auth_code'][0].split('|')[2]

    results = []
    levels = db.Level.select()

    try:
        if data['featured'][0] == 'notpromising':  # moderator recommend not implemented
            if data['sort'][0] == 'popular':
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
            results.append(level_class_to_dict(levels[level], locale))
        except Exception as e:
            print(Exception)
        finally:
            print(level)
    return jsonify(
        {'type': 'detailed_search', 'num_rows': str(num_rows), 'rows_perpage': str(rows_perpage), 'pages': str(pages),
         'result': results})


@app.route('/stage/upload', methods=['POST'])
async def stages_upload_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    locale = data['auth_code'][0].split('|')[2]
    data_swe = data['swe'][0]
    level_id = gen_level_id_md5(data_swe)

    # check non-ASCII
    non_ascii = False
    print((re.sub('[ -~]', '', data['name'][0])))
    if (re.sub('[ -~]', '', data['name'][0])) != "":
        non_ascii = True

    # check duplicated level ID
    not_duplicated = False
    try:
        db.Level.get(db.Level.level_id == level_id)
    except Exception as e:
        print('Not duplicated')
        not_duplicated = True
    finally:
        print('Duplicated, use new ID')

    if not_duplicated:
        level_id = gen_level_id_sha1(data_swe)

    print("Uploading level to storage backend...")
    if len(data_swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return json.dumps({'error_type': '028', 'message': zh_CN.FILE_TOO_LARGE})

    requests.post(url=STORAGE_URL, params={'upload': data['name'][0] + '.swe', 'key': STORAGE_AUTH_KEY},
                  data=data_swe)  # Upload to storage backend

    if locale == 'ES':
        for item in tags_es_to_cn:
            data['tags'][0] = data['tags'][0].replace(item, tags_es_to_cn[item])  # replace ES tags to CN version

    if data['auth_code'][0].split('|')[2] == 'CN':
        data['tags'][0] = data['tags'][0].replace(' ', '')  # Delete the extra spaces in the CN version

    db.add_level(data['name'][0], data['aparience'][0], data['entorno'][0], data['tags'][0],
                 data['auth_code'][0].split('|')[0],
                 level_id, non_ascii)
    if non_ascii:
        if locale == "ES":
            return jsonify({'success': es_ES.UPLOAD_COMPLETE_NON_ASCII, 'id': level_id, 'type': 'upload'})
        else:
            return jsonify({'success': zh_CN.UPLOAD_COMPLETE_NON_ASCII, 'id': level_id, 'type': 'upload'})
    else:
        if locale == "ES":
            return jsonify({'success': es_ES.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'})
        else:
            return jsonify({'success': zh_CN.UPLOAD_COMPLETE, 'id': level_id, 'type': 'upload'})


if __name__ == '__main__':
    db = SMMWEDatabase()
    db.Level.create_table()  # auto create table
    app.run(host=HOST, port=PORT, debug=True)
