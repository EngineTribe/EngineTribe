from dataclasses import dataclass
from peewee import *


class Level(Model):
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


def level_class_to_dict(level_data: Level):
    return {'name': level_data.name, 'likes': str(level_data.likes), 'dislikes': str(level_data.dislikes),
            'comments': '0', 'intentos': str(level_data.intentos), 'muertes': str(level_data.muertes),
            'victorias': str(level_data.victorias), 'apariencia': level_data.apariencia,
            'entorno': level_data.entorno, 'etiquetas': level_data.etiquetas, 'featured': '0',
            'user_data': {'completed': 'no', 'liked': '0'}, 'record': {'record': 'no'}, 'date': level_data.date,
            'author': level_data.author, 'description': 'Sin Descripción', 'archivo': level_data.archivo,
            'id': level_data.id}


def user_login(data):
    login_user = {'username': 'Engine', 'admin': False, 'mod': False, 'booster': False, 'goomba': True,
                  'alias': data['alias'][0],
                  'id': '0000000000', 'uploads': '0',
                  'auth_code': 'ENGINE'}
    if data['token'][0] == Tokens.PC_323:
        login_user['mobile'] = False
    else:
        login_user['mobile'] = True
    return login_user


@dataclass
class Tokens:
    PC_323: str = '282041415'
