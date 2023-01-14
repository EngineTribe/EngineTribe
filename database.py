from peewee import *
from config import *
from locales import *
import datetime

if DATABASE_ADAPTER == 'mysql':
    db_instance = MySQLDatabase(DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER,
                                passwd=DATABASE_PASS, ssl_ca='/etc/ssl/certs/ca-certificates.crt')
elif DATABASE_ADAPTER == 'postgresql':
    db_instance = PostgresqlDatabase(DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER,
                                     passwd=DATABASE_PASS)
elif DATABASE_ADAPTER == 'sqlite':
    db_instance = SqliteDatabase(DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASS)


class SMMWEDatabase:
    def __init__(self):
        self.db_type = DATABASE_ADAPTER
        db_instance.connect()

    class DatabaseModel(Model):
        class Meta:
            database = db_instance

    class Level(DatabaseModel):
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
        non_latin = BooleanField()  # Whether the level name contains non-Latin characters
        featured = BooleanField()  # Whether the level is in promising levels
        record_user = TextField()  # Record user
        record = IntegerField()  # Record
        testing_client = BooleanField()  # For 3.3.0+ testing client
        description = TextField()  # Level description

        # comments = IntegerField()  # Unimplemented in original server

        class Meta:
            table_name = 'level_table'

    class Stats(DatabaseModel):
        level_id = TextField()
        likes_users = TextField()  # Users that liked this level
        dislikes_users = TextField()  # Users that disliked this level

        class Meta:
            table_name = 'stats_table'

    class User(DatabaseModel):
        username = TextField()  # User name
        user_id = TextField()  # Engine Bot is run across IMs, so use string user id
        uploads = IntegerField()  # Upload levels count
        password_hash = TextField()  # Password hash
        is_admin = BooleanField()  # Is administrator
        is_mod = BooleanField()  # Is moderator
        is_booster = BooleanField()  # Is booster
        is_valid = BooleanField()  # Is account valid (Engine-bot determines whether account is still in the QQ group)
        is_banned = BooleanField()  # Is account banned

        class Meta:
            table_name = 'user_table'

    class LevelData(DatabaseModel):  # used in StorageProviderDatabase
        level_id = TextField()  # Level id
        level_data = BlobField()  # Leve data without checksum
        level_checksum = FixedCharField(max_length=40)

        # Store the decoded level data and checksum separately to reduce database usage

        class Meta:
            table_name = 'level_data_table'

    def add_level(self, name, style, environment, tags, author, level_id, non_latin, testing_client, description, locale):
        # add level metadata into database
        tags_id = parse_tag_names(tags, locale)
        level = self.Level(name=name, likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
                           style=style, environment=environment, tag_1=tags_id[0], tag_2=tags_id[1],
                           date=datetime.date.today(), author=author,
                           level_id=level_id, non_latin=non_latin, record_user='', record=0,
                           testing_client=testing_client, description=description)
        level.save()

    def add_user(self, username: str, password_hash: str, user_id):
        # register user
        user = self.User(username=username, password_hash=password_hash, user_id=user_id, uploads=0, is_admin=False,
                         is_mod=False, is_booster=False, is_valid=True, is_banned=False)
        user.save()

    def get_like_type(self, level_id: str, username: str):
        # get like type from database
        try:
            stat = self.Stats.get(self.Stats.level_id == level_id)  # get like data
            if username + ',' in stat.likes_users:
                return '0'  # like
            elif username + ',' in stat.dislikes_users:
                return '1'  # dislike
            else:
                return '3'  # none
        except DoesNotExist:
            return '3'
