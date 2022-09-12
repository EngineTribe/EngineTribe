from dataclasses import dataclass
from peewee import *
import hashlib


def level_class_to_dict(level_data):
    return {'name': level_data.name, 'likes': str(level_data.likes), 'dislikes': str(level_data.dislikes),
            'comments': '0', 'intentos': str(level_data.intentos), 'muertes': str(level_data.muertes),
            'victorias': str(level_data.victorias), 'apariencia': level_data.apariencia,
            'entorno': level_data.entorno, 'etiquetas': level_data.etiquetas, 'featured': '0',
            'user_data': {'completed': 'no', 'liked': '0'}, 'record': {'record': 'no'}, 'date': level_data.date,
            'author': level_data.author, 'description': 'Sin Descripción', 'archivo': level_data.archivo,
            'id': level_data.id}


def user_login(data):
    login_user = {'username': data['alias'][0], 'admin': False, 'mod': False, 'booster': False, 'goomba': True,
                  'alias': data['alias'][0],
                  'id': '0000000000', 'uploads': '0',
                  'auth_code': data['alias'][0]}
    if data['token'][0] == Tokens.PC_323:
        login_user['mobile'] = False
    else:
        login_user['mobile'] = True
    return login_user


def gen_level_id(data_swe: str):
    return prettify_level_id(hashlib.md5(data_swe.encode()).hexdigest().upper()[8:24])


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]


@dataclass
class Tokens:
    PC_323: str = '282041415'
