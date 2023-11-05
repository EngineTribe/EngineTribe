from database.db import Base
from sqlalchemy import Column, Integer, UnicodeText, Text, Date, Boolean, LargeBinary, String, BigInteger, SmallInteger


class Level(Base):
    __table_args = {'mysql_charset': 'utf8mb4'}
    __mapper_args__ = {"eager_defaults": True}
    __tablename__ = "level_table"

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText)  # Level name
    likes = Column(Integer)  # Likes count
    dislikes = Column(Integer)  # Dislikes count
    plays = Column(Integer)  # Play count
    deaths = Column(Integer)  # Death count
    clears = Column(Integer)  # Clear count
    style = Column(SmallInteger)  # Game style
    environment = Column(SmallInteger)  # Level environment
    tag_1 = Column(SmallInteger)  # Tag 1
    tag_2 = Column(SmallInteger)  # Tag 2
    description = Column(UnicodeText)  # Level description
    date = Column(Date)  # Upload date
    author_id = Column(Integer)  # Level maker's ID
    level_id = Column(String(19))  # Level ID
    non_latin = Column(Boolean)  # Whether the level name contains non-Latin characters
    featured = Column(Boolean)  # Whether the level is in promising levels
    record_user_id = Column(Integer)  # Record user's ID
    record = Column(BigInteger)  # Record (ticks)
    testing_client = Column(Boolean)  # For 3.3.0+ testing client


class LikeUsers(Base):
    __tablename__ = "likes_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    user_id = Column(Integer)


class DislikeUsers(Base):
    __tablename__ = "dislikes_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    user_id = Column(Integer)


class ClearedUsers(Base):
    __tablename__ = "clears_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    user_id = Column(Integer)


class User(Base):
    __tablename__ = "user_table"

    id = Column(Integer, primary_key=True)

    username = Column(String(30))  # User name
    im_id = Column(BigInteger)  # User ID (QQ / Telegram)
    uploads = Column(Integer)  # Upload levels count
    password_hash = Column(String(64))  # Password SHA256 hash
    is_admin = Column(Boolean)  # Is administrator
    is_mod = Column(Boolean)  # Is moderator
    is_booster = Column(Boolean)  # Is booster
    is_valid = Column(Boolean)  # Is account valid (Engine-bot determines whether account is still in the QQ group)
    is_banned = Column(Boolean)  # Is account banned


class LevelData(Base):  # used in StorageProviderDatabase
    __tablename__ = "level_data_table"

    id = Column(Integer, primary_key=True)

    level_id = Column(String(19))  # Level id
    level_data = Column(LargeBinary)  # Leve data without checksum
    level_checksum = Column(String(40))  # SHA-1 HMAC checksum


class Client(Base):  # Client tokens
    __tablename__ = "client_table"

    id = Column(Integer, primary_key=True)

    token = Column(String(9))  # Client
    valid = Column(Boolean)  # Whether the token is valid
    type = Column(SmallInteger)  # Client types
    locale = Column(String(2))  # Locale
    mobile = Column(Boolean)  # Is mobile client
    proxied = Column(Boolean)  # Whether to proxy level data
