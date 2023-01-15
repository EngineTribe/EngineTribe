import base64
from dataclasses import dataclass
import hashlib
import aiohttp
import discord
import re

from xpinyin import Pinyin

from locales import *

from config import (
    DISCORD_AVATAR_URL,
    DISCORD_WEBHOOK_URLS,
    ENGINE_BOT_WEBHOOK_URLS
)

from models import LevelDetails, LevelDetailsUserData


@dataclass
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


@dataclass
class AuthCodeData:
    username: str
    platform: str
    locale: str
    locale_item: LocaleModel
    legacy: bool
    testing_client: bool


def level_to_details(level_data, locale: str, generate_url_function, mobile: bool, like_type: str, clear_type: str):
    if mobile and level_data.non_latin:
        name: str = string_latinify(level_data.name)
        description: str = string_latinify(level_data.description)
    else:
        name: str = level_data.name
        description: str = level_data.description
    if level_data.record != 0:
        record = {'record': 'yes', 'alias': level_data.record_user, 'id': '10001', 'time': level_data.record}
    else:
        record = {'record': 'no'}
    return LevelDetails(
        name=name,
        descripcion=description,
        likes=str(level_data.likes),
        dislikes=str(level_data.dislikes),
        comments='0',
        intentos=str(level_data.plays),
        muertes=str(level_data.deaths),
        victorias=str(level_data.clears),
        apariencia=str(level_data.style),
        entorno=str(level_data.environment),
        etiquetas=f'{get_tag_name(level_data.tag_1, locale)},{get_tag_name(level_data.tag_2, locale)}',
        featured=int(level_data.featured),
        user_data=LevelDetailsUserData(
            completed=clear_type,
            liked=like_type
        ),
        date=level_data.date.strftime("%m/%d/%Y"),
        author=level_data.author,
        record=record,
        archivo=generate_url_function(level_data.level_id),
        id=level_data.level_id
    )


def gen_level_id_md5(stripped_swe: str) -> str:
    return prettify_level_id(hashlib.md5(stripped_swe.encode()).hexdigest().upper()[8:24])


def gen_level_id_sha1(stripped_swe: str) -> str:
    return prettify_level_id(hashlib.sha1(stripped_swe.encode()).hexdigest().upper()[8:24])


def gen_level_id_sha256(stripped_swe: str) -> str:
    return prettify_level_id(hashlib.sha256(stripped_swe.encode()).hexdigest().upper()[8:24])


def strip_level(data_swe: str) -> str:
    result = base64.b64decode(data_swe)[:-30].decode("UTF-8")
    regex_time = re.compile('"time": ".*?"')
    regex_date = re.compile('"date": ".*?"')
    result = regex_date.sub('"date": ""', regex_time.sub('"time": ""', result))
    return result


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]


def parse_auth_code(raw_auth_code: str) -> AuthCodeData:
    auth_code_arr = raw_auth_code.split('|')
    locale = auth_code_arr[2]
    match locale:
        case 'CN':
            locale_item = CN
        case 'ES':
            locale_item = ES
        case 'EN':
            locale_item = EN
        case 'PT':
            locale_item = PT
        case 'IT':
            locale_item = IT
        case _:
            locale = 'ES'
            locale_item = ES
    if len(auth_code_arr) == 4:
        if auth_code_arr[3] == 'L':
            # 3.1.5 client
            legacy = True
            testing_client = False
        elif auth_code_arr[3] == 'T':
            # 3.3.0+ testing client
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
    return AuthCodeData(username=auth_code_arr[0], platform=auth_code_arr[1], locale=locale, locale_item=locale_item,
                        legacy=legacy, testing_client=testing_client)


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


async def push_to_engine_bot_qq(data: dict):
    # This function is used to push messages to general Engine Bots
    # (Not limited to QQ)
    # You can construct your own Engine Bot with this API for other IMs
    for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
        async with aiohttp.request(
                method="POST",
                url=webhook_url,
                json=data
        ) as response:
            response_text = await response.text()


async def push_to_engine_bot_discord(message: str):
    async with aiohttp.ClientSession() as session:
        for webhook_url in DISCORD_WEBHOOK_URLS:
            webhook = discord.Webhook.from_url(url=webhook_url, session=session)
            message: str = message
            await webhook.send(message, username="Engine-bot", avatar_url=DISCORD_AVATAR_URL)
