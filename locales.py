import re
from dataclasses import dataclass

tags_cn = ["标准", "解谜", "计时挑战", "自卷轴", "自动图", "一次通过", "对战", "机关", "音乐", "美术", "技巧",
           "射击", "BOSS战", "单人", "Link"]
tags_en = ["Standard", "Puzzle", "Speedrun", "Autoscroll", "Auto-mario", "Short and Sweet",
           "Multiplayer", "Themed", "Music", "Art", "Technical", "Shooter", "Boss battle", "Singleplayer", "Link"]
tags_es = ["Tradicional", "Puzles", "Contrarreloj", "Autoavance", "Automatismos", "Corto pero intenso",
           "Competitivo", "Tematico", "Música", "Artístico", "Habilidad", "Disparos", "Contra jefes",
           "En solitario", "Link"]


@dataclass
class zh_CN:
    UPLOAD_COMPLETE = '上传完成。'
    UPLOAD_COMPLETE_NON_ASCII = '上传完成，但关卡中含有特殊字符，仅对电脑版可见。'
    FILE_TOO_LARGE = '文件大于 4MB。'
    ACCOUNT_NOT_FOUND = '帐号错误或不存在。'
    ACCOUNT_IS_NOT_VALID = '请重新加群。'
    ACCOUNT_BANNED = '玩家已被封禁。'
    ACCOUNT_ERROR_PASSWORD = '密码错误。'
    UPLOAD_LIMIT_REACHED = '关卡数量发布已达上限。'
    LEVEL_NOT_FOUND = '找不到关卡。'
    UPLOAD_CONNECT_ERROR = '连接关卡存储后端失败。'


@dataclass
class es_ES:
    UPLOAD_COMPLETE = 'Publicar completado.'
    UPLOAD_COMPLETE_NON_ASCII = 'Publicar completo, pero con caracteres especiales, solo será visible para PC.'
    FILE_TOO_LARGE = 'El archivo tiene más de 4 MB.'
    ACCOUNT_NOT_FOUND = 'Usuario incorrecto o no encontrado.'
    ACCOUNT_IS_NOT_VALID = 'No autorizado, vuelve a unirte al grupo.'
    ACCOUNT_BANNED = 'Te han prohibido.'
    ACCOUNT_ERROR_PASSWORD = 'Contraseña incorrecta.'
    UPLOAD_LIMIT_REACHED = 'Se alcanzó el máximo de niveles posible para publicar.'
    LEVEL_NOT_FOUND = 'Nivel no encontrado.'
    UPLOAD_CONNECT_ERROR = 'No se pudo conectar al backend de nivel.'


@dataclass
class en_US:
    UPLOAD_COMPLETE = 'Upload completed.'
    UPLOAD_COMPLETE_NON_ASCII = 'Upload completed, but name with special characters, will only be visible on PC.'
    FILE_TOO_LARGE = 'File is bigger than 4MB.'
    ACCOUNT_NOT_FOUND = 'User incorrect or not exists.'
    ACCOUNT_IS_NOT_VALID = 'Not authorized, please rejoin the group'
    ACCOUNT_BANNED = 'User has been banned.'
    ACCOUNT_ERROR_PASSWORD = 'Password incorrect.'
    UPLOAD_LIMIT_REACHED = 'You have reached the upload limit.'
    LEVEL_NOT_FOUND = 'Level not found.'
    UPLOAD_CONNECT_ERROR = 'Could not connect to storage backend.'


def parse_tag_names(tag_names: str):
    tags = tag_names.split(',')
    tag_1 = tags[0]
    tag_2 = tags[1]
    for i in range(0, 15):
        if tags_es[i] == tag_1 or tags_en[i] == tag_1 or tags_cn[i] == tag_1:
            tag_1 = i
        if tags_es[i] == tag_2 or tags_en[i] == tag_2 or tags_cn[i] == tag_2:
            tag_2 = i
    return [tag_1, tag_2]


def get_tag_name(tag_id: int, locale_to: str):
    # The server stores Chinese tag names, so it needs to be converted
    if locale_to == "ES":
        return tags_es[tag_id]
    elif locale_to == "EN":
        return tags_en[tag_id]
    elif locale_to == "CN":
        return tags_cn[tag_id]
