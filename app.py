from flask import Flask, request
from config import *
from peewee import *
import json
from urllib.parse import parse_qs
from smmwe_lib import *

db = MySQLDatabase(DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS)
db.connect()


class BaseModel(Model):
    class Meta:
        database = db


class LevelTable(BaseModel):
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
    id = TextField()  # Level ID
    # description = TextField()  # Unimplemented in original server "Sin Descripción"
    # comments = IntegerField()  # Unimplemented in original server


app = Flask(__name__)

LevelTable.create_table()


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


app.run(host='0.0.0.0', port=PORT, debug=True)
