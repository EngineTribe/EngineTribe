from flask import Flask, request
from config import *
from peewee import *
import json
from urllib.parse import parse_qs, quote
from smmwe_lib import *
import requests
import datetime
from time import strftime

db = MySQLDatabase(DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS)
db.connect()


class BaseModel(Model):
    class Meta:
        database = db


class Level(BaseModel):
    name = TextField()
    likes = IntegerField()
    dislikes = IntegerField()
    intentos = IntegerField()  # Play count
    muertes = IntegerField()  # Death count
    victorias = IntegerField()  # Clear count
    apariencia = TextField()  # Game style
    entorno = TextField()  # Level environment
    etiquetas = TextField()  # The two tags "Tradicional,Puzles"
    date = TextField()  # Upload date "DD/MM/YYYY"
    author = TextField()  # Level maker
    archivo = TextField()  # Level file in storage backend
    level_id = TextField()  # Level ID

    # description = TextField()  # Unimplemented in original server "Sin Descripción"
    # comments = IntegerField()  # Unimplemented in original server
    class Meta:
        table_name = 'level'


app = Flask(__name__)

Level.create_table()


@app.route('/', methods=['GET'])
def website_index():
    return open('website/index.html', 'r').read().replace("${{Markdown}}", open('README.md', 'r').read())


@app.route('/user/login', methods=['POST'])
def user_login_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    return json.dumps(user_login(data))


@app.route('/stages/detailed_search', methods=['POST'])
def stages_detailed_search_handler():
    print('qwq')


@app.route('/stage/upload', methods=['POST'])
def stages_upload_handler():
    data = parse_qs(request.get_data().decode('utf-8'))
    print("Uploading level to storage backend...")
    data_swe = data['swe'][0]
    level_id = gen_level_id(data_swe)
    if len(data_swe.encode()) > 4 * 1024 * 1024:  # 4MB limit
        return json.dumps({'error_type': '028', 'message': 'File is larger than 4MB.'})
    # requests.post(url=STORAGE_URL, params={'upload': data['name'][0] + '.swe', 'key': STORAGE_AUTH_KEY}, data=data_swe)  # Upload to storage backend
    print("Writing level meta to database...")
    level_to_save = Level(name=data['name'][0], likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
                          apariencia=data['aparience'][0], entorno=data['entorno'][0], etiquetas=data['tags'][0],
                          date=datetime.datetime.now().strftime("%m/%d/%Y"), author=data['auth_code'][0],
                          level_id=level_id, archivo=STORAGE_URL + quote(data['name'][0] + '.swe'))
    level_to_save.save()
    return json.dumps({'message': 'Upload completed.', 'error_type': level_id})


app.run(host='0.0.0.0', port=PORT, debug=True)
