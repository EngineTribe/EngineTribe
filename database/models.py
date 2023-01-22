from database.db import Base
from sqlalchemy import Column, Integer, UnicodeText, Text, Date, Boolean, LargeBinary

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
    style = Column(Integer)  # Game style
    environment = Column(Integer)  # Level environment
    tag_1 = Column(Integer)  # Tag 1
    tag_2 = Column(Integer)  # Tag 2
    date = Column(Date)  # Upload date
    author = Column(Text)  # Level maker
    level_id = Column(Text)  # Level ID
    non_latin = Column(Boolean)  # Whether the level name contains non-Latin characters
    featured = Column(Boolean)  # Whether the level is in promising levels
    record_user = Column(Text)  # Record user
    record = Column(Integer)  # Record
    testing_client = Column(Boolean)  # For 3.3.0+ testing client
    description = Column(UnicodeText)  # Level description
    # archivo = Column(Text)  # Level file in storage backend   # deprecated
    # comments = Column(Integer)  # Unimplemented in original server


class LikeUsers(Base):
    __tablename__ = "likes_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    username = Column(Text)


class DislikeUsers(Base):
    __tablename__ = "dislikes_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    username = Column(Text)


class ClearedUsers(Base):
    __tablename__ = "clears_table"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)

    username = Column(Text)


class User(Base):
    __tablename__ = "user_table"

    id = Column(Integer, primary_key=True)

    username = Column(Text)  # User name
    user_id = Column(Text)  # Engine Bot is run across IMs, so user id is string
    uploads = Column(Integer)  # Upload levels count
    password_hash = Column(Text)  # Password hash
    is_admin = Column(Boolean)  # Is administrator
    is_mod = Column(Boolean)  # Is moderator
    is_booster = Column(Boolean)  # Is booster
    is_valid = Column(Boolean)  # Is account valid (Engine-bot determines whether account is still in the QQ group)
    is_banned = Column(Boolean)  # Is account banned


class LevelData(Base):  # used in StorageProviderDatabase
    __tablename__ = "level_data_table"

    id = Column(Integer, primary_key=True)

    level_id = Column(Text)  # Level id
    level_data = Column(LargeBinary)  # Leve data without checksum
    level_checksum = Column(Text)  # SHA-1 HMAC checksum


class Stats(Base):
    __tablename__ = "stats_table"

    id = Column(Integer, primary_key=True)

    level_id = Column(Text)  # Level id
    likes_users = Column(Text)
    dislikes_users = Column(Text)
