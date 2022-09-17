from peewee import *
from config import *
import datetime
from urllib.parse import quote

db = MySQLDatabase(DB_NAME, host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS)


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

    def add_level(self, name, apariencia, entorno, etiquetas, author, level_id, non_ascii):
        level = self.Level(name=name, likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
                           apariencia=apariencia, entorno=entorno, etiquetas=etiquetas,
                           date=datetime.datetime.now().strftime("%m/%d/%Y"), author=author,
                           level_id=level_id, archivo=STORAGE_URL + quote(name + '.swe'), non_ascii=non_ascii)
        level.save()
