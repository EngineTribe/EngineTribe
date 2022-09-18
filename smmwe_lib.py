from dataclasses import dataclass
from locales import *
import hashlib


def level_class_to_dict(level_data, locale: str, proxied: bool, convert_url_function):
    tags = level_data.etiquetas
    if locale == 'ES':
        for item in tags_es_to_cn:
            tags = tags.replace(tags_es_to_cn[item], item)  # replace CN tags to ES version
    if proxied:
        url = convert_url_function(level_data.archivo)
    else:
        url = level_data.archivo
    return {'name': level_data.name, 'likes': str(level_data.likes), 'dislikes': str(level_data.dislikes),
            'comments': '0', 'intentos': str(level_data.intentos), 'muertes': str(level_data.muertes),
            'victorias': str(level_data.victorias), 'apariencia': level_data.apariencia,
            'entorno': level_data.entorno, 'etiquetas': tags, 'featured': '0',
            'user_data': {'completed': 'no', 'liked': '1'}, 'record': {'record': 'no'}, 'date': level_data.date,
            'author': level_data.author, 'description': 'Sin Descripción', 'archivo': url,
            'id': level_data.level_id}


def gen_level_id_md5(data_swe: str):
    return prettify_level_id(hashlib.md5(data_swe.encode()).hexdigest().upper()[8:24])


def gen_level_id_sha1(data_swe: str):
    return prettify_level_id(hashlib.sha1(data_swe.encode()).hexdigest().upper()[8:24])


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]


@dataclass
class Tokens:
    PC_CN: str = 'SMMWEPCCN'
    PC_ES: str = 'SMMWEPCES'
