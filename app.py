import json

import requests
from flask import Flask, request, jsonify
from urllib.parse import parse_qs

from config import *
from database import SMMWEDatabase
from smmwe_lib import *

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
    if data['token'][0] == Tokens.PC_323:
        login_user['mobile'] = False
        login_user['auth_code'] = data['alias'][0] + '|PC'
    else:
        login_user['mobile'] = True
        login_user['auth_code'] = data['alias'][0] + '|Mobile'
    return jsonify(login_user)


@app.route('/stages/detailed_search', methods=['POST'])
async def stages_detailed_search_handler():
    return 'qwq'


@app.route('/stage/upload', methods=['POST'])
async def stages_upload_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    print("Uploading level to storage backend...")
    data_swe = data['swe'][0]
    level_id = gen_level_id(data_swe)
    if len(data_swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return json.dumps({'error_type': '028', 'message': 'File is larger than 4MB.'})
    requests.post(url=STORAGE_URL, params={'upload': data['name'][0] + '.swe', 'key': STORAGE_AUTH_KEY},
                  data=data_swe)  # Upload to storage backend
    db.add_level(data['name'][0], data['aparience'][0], data['entorno'][0], data['tags'][0], data['auth_code'][0],
                 level_id)
    return jsonify({'message': 'Upload completed.', 'error_type': level_id})


if __name__ == '__main__':
    db = SMMWEDatabase()
    db.Level.create_table()  # auto create table
    app.run(host=HOST, port=PORT, debug=True)
