from peewee import *
from config import *
import datetime
from urllib.parse import quote

if DB_TYPE == 'mysql':
    db = MySQLDatabase(DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS)
elif DB_TYPE == 'postgres':
    db = PostgresqlDatabase(DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS)
elif DB_TYPE == 'sqlite':
    db = SqliteDatabase(DB_HOST, user=DB_USER, passwd=DB_PASS)


class SMMWEDatabase:
    def __init__(self):
        db.connect()

    class BaseModel(Model):
        class Meta:
            database = db

    class Level(BaseModel):
        name = TextField()
        likes = IntegerField()
        dislikes = IntegerField()
        intentos = IntegerField()  # Play count
        muertes = IntegerField()  # Death count
        victorias = IntegerField()  # Clear count
        apariencia = TextField()  # Game style
        entorno = TextField()  # Level environment
        etiquetas = TextField()  # The two tags "Tradicional,Puzles"
        date = TextField()  # Upload date "DD/MM/YYYY"
        author = TextField()  # Level maker
        archivo = TextField()  # Level file in storage backend
        level_id = TextField()  # Level ID
        non_ascii = BooleanField()  # Whether the level name contains non-ASCII characters

        # description = TextField()  # Unimplemented in original server "Sin Descripción"
        # comments = IntegerField()  # Unimplemented in original server

        class Meta:
            table_name = 'level_table'

    class Account(BaseModel):
        name = TextField()  # User name
        qq_id = TextField()  # Since Engine-bot is hosted on QQ, use QQ ID instead of original Discord ID
        uploads = IntegerField()  # Upload levels count
        password_hash = TextField()  # Password hash
        is_admin = BooleanField()  # Is administrator
        is_mod = BooleanField()  # Is moderator
        is_booster = BooleanField()  # Is booster (not implemented now but planned)
        is_valid = BooleanField()  # Is account valid (Engine-bot determines whether account is still in the QQ group)
        is_banned = BooleanField()  # Is account banned

        class Meta:
            table_name = 'account_table'

    def add_level(self, name, apariencia, entorno, etiquetas, author, level_id, non_ascii):
        level = self.Level(name=name, likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
                           apariencia=apariencia, entorno=entorno, etiquetas=etiquetas,
                           date=datetime.datetime.now().strftime("%m/%d/%Y"), author=author,
                           level_id=level_id, archivo=STORAGE_URL + quote(name + '.swe'), non_ascii=non_ascii)
        level.save()
