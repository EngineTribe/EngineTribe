import base64
import hashlib
from urllib.parse import parse_qs, quote
from xpinyin import Pinyin

from locales import *


def level_db_to_dict(level_data, locale: str, generate_url_function, mobile: bool, like_type: str):
    url = generate_url_function(level_data.name, level_data.level_id)
    if mobile:
        name = string_asciify(level_data.name)
    else:
        name = level_data.name
    if level_data.plays > 0:
        record = {'record': 'yes', 'alias': 'EngineTribe', 'id': '0', 'time': 0}
    else:
        record = {'record': 'no'}
    return {'name': name, 'likes': str(level_data.likes), 'dislikes': str(level_data.dislikes),
            'comments': '0', 'intentos': str(level_data.plays), 'muertes': str(level_data.deaths),
            'victorias': str(level_data.clears), 'apariencia': level_data.style,
            'entorno': level_data.environment,
            'etiquetas': get_tag_name(level_data.tag_1, locale) + ',' + get_tag_name(level_data.tag_2, locale),
            'featured': int(level_data.featured),
            'user_data': {'completed': 'no', 'liked': like_type}, 'record': record,
            'date': level_data.date.strftime("%m/%d/%Y"),
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


def calculate_password_hash(password: str):
    return hashlib.sha256(base64.b64encode(password.encode('utf-8'))).hexdigest()


def string_asciify(t):
    table = {ord(f): ord(t) for f, t in zip(u'，。！？【】（）％＃＠＆－—〔〕：；〇﹒—﹙﹚、—', u',.!?[]()%#@&--():;0.—(),-')}

    try:
        t2 = t.translate(table)
    except:
        t2 = t
    t2 = Pinyin().get_pinyin(t2).replace('-', ' ')
    t2 = quote(t2, safe='"!@#$%^&*()-_=+[{]}\'\\|:;,<.>/?`~ ')
    return t2


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
