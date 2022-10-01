from peewee import *
from config import *
from locales import *
import datetime

if DATABASE_ADAPTER == 'mysql':
    db = MySQLDatabase(DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER, passwd=DATABASE_PASS)
elif DATABASE_ADAPTER == 'postgres':
    db = PostgresqlDatabase(DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER,
                            passwd=DATABASE_PASS)
elif DATABASE_ADAPTER == 'sqlite':
    db = SqliteDatabase(DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASS)


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
        plays = IntegerField()  # Play count
        deaths = IntegerField()  # Death count
        clears = IntegerField()  # Clear count
        style = TextField()  # Game style
        environment = TextField()  # Level environment
        tag_1 = IntegerField()  # Tag 1
        tag_2 = IntegerField()  # Tag 2
        date = DateField()  # Upload date
        author = TextField()  # Level maker
        # archivo = TextField()  # Level file in storage backend   # deprecated
        level_id = TextField()  # Level ID
        non_ascii = BooleanField()  # Whether the level name contains non-ASCII characters
        featured = BooleanField()  # Whether the level is in promising levels

        # description = TextField()  # Unimplemented in original server "Sin Descripción"
        # comments = IntegerField()  # Unimplemented in original server

        class Meta:
            table_name = 'level_table'

    class Stats(BaseModel):
        level_id = TextField()
        likes_users = TextField()  # Users that liked this level
        dislikes_users = TextField()  # Users that disliked this level

        class Meta:
            table_name = 'stats_table'

    class User(BaseModel):
        username = TextField()  # User name
        user_id = TextField()  # Since Engine-bot is hosted on QQ, use QQ ID instead of original Discord ID
        uploads = IntegerField()  # Upload levels count
        password_hash = TextField()  # Password hash
        is_admin = BooleanField()  # Is administrator
        is_mod = BooleanField()  # Is moderator
        is_booster = BooleanField()  # Is booster (not implemented now but planned)
        is_valid = BooleanField()  # Is account valid (Engine-bot determines whether account is still in the QQ group)
        is_banned = BooleanField()  # Is account banned

        class Meta:
            table_name = 'user_table'

    def add_level(self, name, style, environment, tags, author, level_id, non_ascii):
        tags_id = parse_tag_names(tags)
        level = self.Level(name=name, likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
                           style=style, environment=environment, tag_1=tags_id[0], tag_2=tags_id[1],
                           date=datetime.date.today(), author=author,
                           level_id=level_id, non_ascii=non_ascii)
        level.save()

    def add_user(self, username, password_hash, user_id):
        user = self.User(username=username, password_hash=password_hash, user_id=user_id, uploads=0,
                            is_admin=False, is_mod=False, is_booster=False, is_valid=True, is_banned=False)
        user.save()
