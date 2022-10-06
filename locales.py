import re
from pydantic import BaseModel as PydanticModel

tags_cn = ["标准", "解谜", "计时挑战", "自卷轴", "自动图", "一次通过", "对战", "机关", "音乐", "美术", "技巧",
           "射击", "BOSS战", "单人", "Link", "---"]
tags_en = ["Standard", "Puzzle", "Speedrun", "Autoscroll", "Auto-mario", "Short and Sweet", "Multiplayer",
           "Themed", "Music", "Art", "Technical", "Shooter", "Boss battle", "Singleplayer", "Link", "---"]
tags_es = ["Tradicional", "Puzles", "Contrarreloj", "Autoavance", "Automatismos", "Corto pero intenso",
           "Competitivo", "Tematico", "Música", "Artístico", "Habilidad", "Disparos", "Contra jefes",
           "En solitario", "Link", "---"]


class LocaleModel:
    UPLOAD_COMPLETE: str
    FILE_TOO_LARGE: str
    ACCOUNT_NOT_FOUND: str
    ACCOUNT_IS_NOT_VALID: str
    ACCOUNT_BANNED: str
    ACCOUNT_ERROR_PASSWORD: str
    UPLOAD_LIMIT_REACHED: str
    LEVEL_NOT_FOUND: str
    UPLOAD_CONNECT_ERROR: str
    LEVEL_ID_REPEAT: str
    NOT_IMPLEMENTED: str


class zh_CN(LocaleModel):
    UPLOAD_COMPLETE: str = '上传完成。'
    FILE_TOO_LARGE: str = '文件大于 4MB。'
    ACCOUNT_NOT_FOUND: str = '帐号错误或不存在。'
    ACCOUNT_IS_NOT_VALID: str = '请重新加群。'
    ACCOUNT_BANNED: str = '玩家已被封禁。'
    ACCOUNT_ERROR_PASSWORD: str = '密码错误。'
    UPLOAD_LIMIT_REACHED: str = '关卡数量发布已达上限。'
    LEVEL_NOT_FOUND: str = '找不到关卡。'
    UPLOAD_CONNECT_ERROR: str = '连接关卡存储后端失败。'
    LEVEL_ID_REPEAT: str = '关卡已存在'
    NOT_IMPLEMENTED: str = '未实现。'


class es_ES(LocaleModel):
    UPLOAD_COMPLETE: str = 'Publicar completado.'
    FILE_TOO_LARGE: str = 'El archivo tiene más de 4 MB.'
    ACCOUNT_NOT_FOUND: str = 'Usuario incorrecto o no encontrado.'
    ACCOUNT_IS_NOT_VALID: str = 'No autorizado, vuelve a unirte al grupo.'
    ACCOUNT_BANNED: str = 'Te han prohibido.'
    ACCOUNT_ERROR_PASSWORD: str = 'Contraseña incorrecta.'
    UPLOAD_LIMIT_REACHED: str = 'Se alcanzó el máximo de niveles posible para publicar.'
    LEVEL_NOT_FOUND: str = 'Nivel no encontrado.'
    UPLOAD_CONNECT_ERROR: str = 'No se pudo conectar al backend de nivel.'
    LEVEL_ID_REPEAT: str = 'El nivel ya existe.'
    NOT_IMPLEMENTED: str = 'No se ha implementado.'


class en_US(LocaleModel):
    UPLOAD_COMPLETE: str = 'Upload completed.'
    FILE_TOO_LARGE: str = 'File is bigger than 4MB.'
    ACCOUNT_NOT_FOUND: str = 'User incorrect or doesn\'t exist'
    ACCOUNT_IS_NOT_VALID: str = 'Not authorized, please rejoin the group'
    ACCOUNT_BANNED: str = 'User has been banned.'
    ACCOUNT_ERROR_PASSWORD: str = 'Password incorrect.'
    UPLOAD_LIMIT_REACHED: str = 'You have reached the upload limit.'
    LEVEL_NOT_FOUND: str = 'Level not found.'
    UPLOAD_CONNECT_ERROR: str = 'Could not connect to the storage backend.'
    LEVEL_ID_REPEAT: str = 'Level already exists.'
    NOT_IMPLEMENTED: str = 'Not implemented.'


def parse_tag_names(tag_names: str):
    tags = tag_names.split(',')
    tag_1 = tags[0].strip()
    tag_2 = tags[1].strip()
    for i in range(0, 16):
        if tags_es[i] == tag_1 or tags_en[i] == tag_1 or tags_cn[i] == tag_1:
            tag_1 = i
        if tags_es[i] == tag_2 or tags_en[i] == tag_2 or tags_cn[i] == tag_2:
            tag_2 = i
    return [tag_1, tag_2]


def get_tag_name(tag_id: int, locale_to: str):
    if locale_to == "ES":
        return tags_es[tag_id]
    elif locale_to == "EN":
        return tags_en[tag_id]
    elif locale_to == "CN":
        return tags_cn[tag_id]
