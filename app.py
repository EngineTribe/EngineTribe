import json

import requests
from aiohttp import web

from config import *
from database import SMMWEDatabase
from smmwe_lib import *


async def readme_handler(request):
    return web.Response(
        text=open('website/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read()),
        content_type='text/html')


async def user_login_handler(request):
    data = await request.args.to_dict()
    login_user = {'username': data['alias'], 'admin': False, 'mod': False, 'booster': False, 'goomba': True,
                  'alias': data['alias'],
                  'id': '0000000000', 'uploads': '0',
                  'auth_code': data['alias']}
    if data['token'][0] == Tokens.PC_323:
        login_user['mobile'] = False
    else:
        login_user['mobile'] = True
    return web.json_response(login_user)


async def stages_detailed_search_handler(request):
    return web.Response(text='qwq')


async def stages_upload_handler(request):
    data = request.args.to_dict()
    print("Uploading level to storage backend...")
    data_swe = data['swe']
    level_id = gen_level_id(data_swe)
    if len(data_swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return json.dumps({'error_type': '028', 'message': 'File is larger than 4MB.'})
    requests.post(url=STORAGE_URL, params={'upload': data['name'] + '.swe', 'key': STORAGE_AUTH_KEY},
                  data=data_swe)  # Upload to storage backend
    db.add_level(data['name'], data['aparience'], data['entorno'], data['tags'], data['auth_code'], level_id)
    return web.json_response({'message': 'Upload completed.', 'error_type': level_id})


if __name__ == '__main__':
    db = SMMWEDatabase()
    db.Level.create_table()  # auto create table
    app = web.Application()
    app.add_routes([web.get('/', readme_handler),
                    web.post('/user/login', user_login_handler),
                    web.post('/stages/detailed_search', stages_detailed_search_handler),
                    web.post('/stage/upload', stages_upload_handler)])
    web.run_app(app, host=HOST, port=PORT)
