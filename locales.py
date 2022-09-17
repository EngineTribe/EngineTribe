from dataclasses import dataclass


@dataclass
class zh_CN:
    UPLOAD_COMPLETE = '上传完成。'
    UPLOAD_COMPLETE_NON_ASCII = '上传完成，但关卡中含有特殊字符，仅对电脑版可见。'
    FILE_TOO_LARGE = '文件大于 4MB。'


@dataclass
class es_ES:
    UPLOAD_COMPLETE = 'Publicar completado.'
    UPLOAD_COMPLETE_NON_ASCII = 'Publicar completo, pero con caracteres especiales, solo será visible para PC.'
    FILE_TOO_LARGE = 'El archivo tiene más de 4 MB.'


tags_es_to_cn = {
    "Tradicional": "标准",
    "Puzles": "解谜",
    "Contrarreloj": "计时挑战",
    "Autoavance": "自卷轴",
    "Automatismos": "自动图",
    "Corto pero intenso": "一次通过",
    "Competitivo": "对战",
    "Tematico": "机关",
    "Música": "音乐",
    "Artístico": "美术",
    "Habilidad": "技巧",
    "Disparos": "射击",
    "Contra jefes": "BOSS战",
    "En solitario": "单人"}
