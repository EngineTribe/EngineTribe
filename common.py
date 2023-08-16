import base64
from dataclasses import dataclass
from enum import Enum
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

from database.models import Level

from models import LevelDetails, LevelDetailsUserData


class ClientType(Enum):
    STABLE = 1
    TESTING = 2
    LEGACY = 3
    ENGINE_BOT = 4


@dataclass
class AuthCodeData:
    user_id: int
    platform: str
    locale: str
    locale_item: LocaleModel
    legacy: bool
    testing_client: bool


def level_to_details(level_data: Level, locale: str, level_file_url: str, mobile: bool, like_type: str,
                     clear_type: str,
                     author: str, record_user: str):
    if mobile and level_data.non_latin:
        name: str = string_latinify(level_data.name)
    else:
        name: str = level_data.name
    if level_data.record != 0:
        record = {'record': 'yes',
                  'alias': record_user,
                  'id': level_data.record_user_id,
                  'time': level_data.record}
    else:
        record = {'record': 'no'}

    desc = level_data.description
    if desc == '' or desc is None:
        desc = 'Sin descripción'

    return LevelDetails(
        name=name,
        likes=level_data.likes,
        dislikes=level_data.dislikes,
        comments=0,
        intentos=level_data.plays,
        muertes=level_data.deaths,
        victorias=level_data.clears,
        apariencia=level_data.style,
        entorno=level_data.environment,
        etiquetas=f'{prettify_tag_name(level_data.tag_1, locale)},{prettify_tag_name(level_data.tag_2, locale)}',
        featured=int(level_data.featured),
        user_data=LevelDetailsUserData(
            completed=clear_type,
            liked=like_type
        ),
        date=level_data.date.strftime("%m/%d/%Y"),
        author=author,
        record=record,
        archivo=level_file_url,
        id=level_data.level_id,
        descripcion=desc,
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
