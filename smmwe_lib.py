import base64
import hashlib

from xpinyin import Pinyin

from locales import *


def level_db_to_dict(level_data, locale: str, generate_url_function, mobile: bool, like_type: str):
    url = generate_url_function(level_data.level_id)
    if mobile and level_data.non_latin:
        name = string_latinify(level_data.name)
    else:
        name = level_data.name
    # print(level_data.name)
    if level_data.record != 0:
        record = {'record': 'yes', 'alias': level_data.record_user, 'id': '10001', 'time': level_data.record}
    else:
        record = {'record': 'no'}
    return {'name': name,
            'likes': str(level_data.likes),
            'dislikes': str(level_data.dislikes),
            'comments': '0',
            'intentos': str(level_data.plays),
            'muertes': str(level_data.deaths),
            'victorias': str(level_data.clears),
            'apariencia': level_data.style,
            'entorno': level_data.environment,
            'etiquetas': get_tag_name(level_data.tag_1, locale) + ',' + get_tag_name(level_data.tag_2, locale),
            'featured': int(level_data.featured),
            'user_data': {'completed': 'no', 'liked': like_type},
            'record': record,
            'date': level_data.date.strftime("%m/%d/%Y"),
            'author': level_data.author,
            'description': 'Sin Descripción',
            'archivo': url,
            'id': level_data.level_id}


def gen_level_id_md5(data_swe: str):
    return prettify_level_id(hashlib.md5(data_swe.encode()).hexdigest().upper()[8:24])


def gen_level_id_sha1(data_swe: str):
    return prettify_level_id(hashlib.sha1(data_swe.encode()).hexdigest().upper()[8:24])


def gen_level_id_sha256(data_swe: str):
    return prettify_level_id(hashlib.sha256(data_swe.encode()).hexdigest().upper()[8:24])


def strip_level(data_swe: str):
    result = base64.b64decode(data_swe)[:-30].decode("UTF-8")
    regex_time = re.compile('"time": ".*?"')
    regex_date = re.compile('"date": ".*?"')
    result = regex_date.sub('"date": ""', regex_time.sub('"time": ""', result))
    return result


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]


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
    if len(auth_code_arr) == 4:
        if auth_code_arr[3] == 'L':
            # 3.1.5 client
            legacy = True
            testing_client = False
        elif auth_code_arr[3] == 'T':
            # 3.2.4 testing client
            legacy = False
            testing_client = True
        else:
            # other client
            legacy = False
            testing_client = False
    else:
        # 3.2.3 client
        legacy = False
        testing_client = False
    return_data = AuthCodeData()
    return_data.username = auth_code_arr[0]
    return_data.platform = auth_code_arr[1]
    return_data.locale = locale
    return_data.locale_item = locale_item
    return_data.legacy = legacy
    return_data.testing_client = testing_client
    return return_data


def calculate_password_hash(password: str):
    return hashlib.sha256(base64.b64encode(password.encode('utf-8'))).hexdigest()


def string_latinify(t):
    table = {ord(f): ord(t) for f, t in zip(u'，。！？【】（）％＃＠＆－—〔〕：；〇﹒—﹙﹚、—“”', u',.!?[]()%#@&--():;0.—(),-""')}

    try:
        t2 = t.translate(table)
    except:
        t2 = t
    t2 = Pinyin().get_pinyin(t2).replace('-', ' ')
    t2 = re.sub(u'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]', u'', t2)
    return t2


def is_valid_user_agent(user_agent):
    if user_agent:
        if 'GameMaker' in user_agent or 'Android' in user_agent or 'EngineBot' in user_agent:
            return True
        else:
            return False
    else:
        return False


class Tokens:
    PC_CN: str = 'SMMWEPCCN'
    PC_ES: str = 'SMMWEPCES'
    PC_EN: str = 'SMMWEPCEN'
    Mobile_CN: str = 'SMMWEMBCN'
    Mobile_ES: str = 'SMMWEMBES'
    Mobile_EN: str = 'SMMWEMBEN'
    PC_Legacy_CN: str = 'LEGACPCCN'
    PC_Legacy_ES: str = 'LEGACPCES'
    PC_Legacy_EN: str = 'LEGACPCEN'
    Mobile_Legacy_CN: str = 'LEGACMBCN'
    Mobile_Legacy_ES: str = 'LEGACMBES'
    Mobile_Legacy_EN: str = 'LEGACMBEN'
    PC_Testing_CN: str = 'TESTCPCCN'
    PC_Testing_ES: str = 'TESTCPCES'
    PC_Testing_EN: str = 'TESTCPCEN'
    Mobile_Testing_CN: str = 'TESTCMBCN'
    Mobile_Testing_ES: str = 'TESTCMBES'
    Mobile_Testing_EN: str = 'TESTCMBEN'


class AuthCodeData:
    username: str
    platform: str
    locale: str
    locale_item: LocaleModel
    legacy: bool
    testing_client: bool
