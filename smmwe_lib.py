from dataclasses import dataclass
from locales import *
import hashlib
from urllib.parse import parse_qs


def level_class_to_dict(level_data, locale: str, proxied: bool, convert_url_function):
    tags = convert_tags('CN', locale, level_data.etiquetas)
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


def gen_level_id_sha256(data_swe: str):
    return prettify_level_id(hashlib.sha256(data_swe.encode()).hexdigest().upper()[8:24])


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]


def parse_data(request):
    data = parse_qs(request.get_data().decode('utf-8'))
    for item in data:
        data[item] = data[item][0]
    return data


def parse_auth_code(raw_auth_code: str):
    auth_code_arr = raw_auth_code.split('|')
    locale = auth_code_arr[2]
    if locale == 'CN':
        locale_item = zh_CN
    elif locale == 'ES':
        locale_item = es_ES
    elif locale == 'EN':
        locale_item = en_US
    else:
        locale_item = es_ES
    return AuthCodeData(username=auth_code_arr[0], platform=auth_code_arr[1], locale=locale, locale_item=locale_item)


@dataclass
class Tokens:
    PC_CN: str = 'SMMWEPCCN'
    PC_ES: str = 'SMMWEPCES'
    PC_EN: str = 'SMMWEPCEN'
    Mobile_CN: str = 'SMMWEMBCN'
    Mobile_ES: str = 'SMMWEMBES'
    Mobile_EN: str = 'SMMWEMBEN'


@dataclass
class AuthCodeData:
    username: str
    platform: str
    locale: str
    locale_item: any
