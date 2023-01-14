from dataclasses import dataclass

tags_cn = ["标准", "解谜", "计时挑战", "自卷轴", "自动图", "一次通过", "对战", "机关", "音乐", "美术", "技巧",
           "射击", "BOSS战", "单人", "Link", "---"]
tags_en = ["Standard", "Puzzle", "Speedrun", "Autoscroll", "Auto-mario", "Short and Sweet", "Multiplayer",
           "Themed", "Music", "Art", "Technical", "Shooter", "Boss battle", "Singleplayer", "Link", "---"]
tags_es = ["Tradicional", "Puzles", "Contrarreloj", "Autoavance", "Automatismos", "Corto pero intenso",
           "Competitivo", "Tematico", "Música", "Artístico", "Habilidad", "Disparos", "Contra jefes",
           "En solitario", "Link", "---"]
tags_pt = ["Tradicional", "Puzles", "Contrarreloj", "Autoavance", "Automatismos", "Corto pero intenso",
           "Competitivo", "Tematico", "Música", "Artístico", "Habilidad", "Disparos", "Contra jefes",
           "En solitario", "Link", "---"]  # I didn't find Portuguese text in SMM2, so put it aside for now
tags_it = ["Classico", "Rompicapi", "Corsa", "Scorrimento", "Automatico", "Corto ma bello", "Competizione",
           "Tematico", "Musica", "Artistico", "Tecnico", "Sparatutto", "Scontro col boss", "Un giocatore",
           "Link", "---"]


@dataclass
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
    UNKNOWN_DIFFICULTY: str
    UNKNOWN_QUERY_MODE: str
    LEVEL_ID_REPEAT: str
    NOT_IMPLEMENTED: str


@dataclass
class CN(LocaleModel):
    UPLOAD_COMPLETE: str = '上传完成。'
    FILE_TOO_LARGE: str = '文件大于 4MB。'
    ACCOUNT_NOT_FOUND: str = '帐号错误或不存在。'
    ACCOUNT_IS_NOT_VALID: str = '请重新加群。'
    ACCOUNT_BANNED: str = '玩家已被封禁。'
    ACCOUNT_ERROR_PASSWORD: str = '密码错误。'
    UPLOAD_LIMIT_REACHED: str = '关卡发布数量已达上限。'
    LEVEL_NOT_FOUND: str = '找不到关卡。'
    UPLOAD_CONNECT_ERROR: str = '连接关卡存储后端失败。'
    UNKNOWN_DIFFICULTY: str = '未知难度。'
    UNKNOWN_QUERY_MODE: str = '未知查询模式。'
    LEVEL_ID_REPEAT: str = '关卡已存在'
    NOT_IMPLEMENTED: str = '未实现。'


@dataclass
class ES(LocaleModel):
    UPLOAD_COMPLETE: str = 'Publicar completado.'
    FILE_TOO_LARGE: str = 'El archivo tiene más de 4 MB.'
    ACCOUNT_NOT_FOUND: str = 'Usuario incorrecto o no encontrado.'
    ACCOUNT_IS_NOT_VALID: str = 'No autorizado porque no estás en el servidor.'
    ACCOUNT_BANNED: str = 'Te han prohibido.'
    ACCOUNT_ERROR_PASSWORD: str = 'Contraseña incorrecta.'
    UPLOAD_LIMIT_REACHED: str = 'Se alcanzó el máximo de niveles posible para publicar.'
    LEVEL_NOT_FOUND: str = 'Nivel no encontrado.'
    UPLOAD_CONNECT_ERROR: str = 'No se pudo conectar al backend de nivel.'
    UNKNOWN_DIFFICULTY: str = 'Dificultad desconocida.'
    UNKNOWN_QUERY_MODE: str = 'Modo de consulta desconocido.'
    LEVEL_ID_REPEAT: str = 'El nivel ya existe.'
    NOT_IMPLEMENTED: str = 'No se ha implementado.'


@dataclass
class EN(LocaleModel):
    UPLOAD_COMPLETE: str = 'Upload completed.'
    FILE_TOO_LARGE: str = 'File is bigger than 4MB.'
    ACCOUNT_NOT_FOUND: str = 'User incorrect or doesn\'t exist.'
    ACCOUNT_IS_NOT_VALID: str = 'Not authorized because you are not in the server.'
    ACCOUNT_BANNED: str = 'User has been banned.'
    ACCOUNT_ERROR_PASSWORD: str = 'Password incorrect.'
    UPLOAD_LIMIT_REACHED: str = 'You have reached the upload limit.'
    LEVEL_NOT_FOUND: str = 'Level not found.'
    UPLOAD_CONNECT_ERROR: str = 'Could not connect to the storage backend.'
    UNKNOWN_DIFFICULTY: str = 'Unknown difficulty.'
    UNKNOWN_QUERY_MODE: str = 'Unknown query mode.'
    LEVEL_ID_REPEAT: str = 'Level already exists.'
    NOT_IMPLEMENTED: str = 'Not implemented.'


@dataclass
class PT(LocaleModel):
    UPLOAD_COMPLETE: str = 'Carregamento concluído.'
    FILE_TOO_LARGE: str = 'O arquivo é maior que 4 MB.'
    ACCOUNT_NOT_FOUND: str = 'Usuário incorreto ou não existe.'
    ACCOUNT_IS_NOT_VALID: str = 'Não autorizado porque você não está no servidor.'
    ACCOUNT_BANNED: str = 'O usuário foi banido.'
    ACCOUNT_ERROR_PASSWORD: str = 'Senha incorreta.'
    UPLOAD_LIMIT_REACHED: str = 'Você atingiu o limite de upload.'
    LEVEL_NOT_FOUND: str = 'Nível não encontrado.'
    UPLOAD_CONNECT_ERROR: str = 'Não foi possível conectar ao back-end de armazenamento.'
    UNKNOWN_DIFFICULTY: str = 'Dificuldade desconhecida.'
    UNKNOWN_QUERY_MODE: str = 'Modo de consulta desconhecido.'
    LEVEL_ID_REPEAT: str = 'O nível já existe.'
    NOT_IMPLEMENTED: str = 'Não implementado.'


@dataclass
class IT(LocaleModel):
    UPLOAD_COMPLETE: str = 'Caricamento completato.'
    FILE_TOO_LARGE: str = 'Il file è più grande di 4 MB.'
    ACCOUNT_NOT_FOUND: str = 'Utente errato o inesistente.'
    ACCOUNT_IS_NOT_VALID: str = 'Non autorizzato perché non sei nel server.'
    ACCOUNT_BANNED: str = 'L\'utente è stato bannato.'
    ACCOUNT_ERROR_PASSWORD: str = 'Password non corretta.'
    UPLOAD_LIMIT_REACHED: str = 'Hai raggiunto il limite di caricamento.'
    LEVEL_NOT_FOUND: str = 'Livello non trovato.'
    UPLOAD_CONNECT_ERROR: str = 'Impossibile connettersi al back-end di archiviazione.'
    UNKNOWN_DIFFICULTY: str = 'Difficoltà sconosciuta.'
    UNKNOWN_QUERY_MODE: str = 'Modalità query sconosciuta.'
    LEVEL_ID_REPEAT: str = 'Il livello esiste già.'
    NOT_IMPLEMENTED: str = 'Non implementato.'


def parse_tag_names(tag_names: str, locale: str) -> list:
    tags = tag_names.split(',')
    tag_1 = tags[0].strip()
    tag_2 = tags[1].strip()
    tags_list: list = []
    match locale:
        case "ES":
            tags_list = tags_es
        case "EN":
            tags_list = tags_en
        case "CN":
            tags_list = tags_cn
        case "PT":
            tags_list = tags_pt
        case "IT":
            tags_list = tags_it
    for i in range(0, 16):
        if tags_list[i] == tag_1:
            tag_1 = i
        if tags_list[i] == tag_2:
            tag_2 = i
    return [tag_1, tag_2]


def get_tag_name(tag_id: int, locale_to: str) -> str:
    match locale_to:
        case "ES":
            return tags_es[tag_id]
        case "EN":
            return tags_en[tag_id]
        case "CN":
            return tags_cn[tag_id]
        case "PT":
            return tags_pt[tag_id]
        case "IT":
            return tags_it[tag_id]
