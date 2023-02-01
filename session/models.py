from session.db import Base
from sqlalchemy import Column, Integer, Boolean, String, BigInteger, SmallInteger


class Session(Base):
    __tablename__ = "session_table"
    id = Column(Integer, primary_key=True)
    username = Column(String(30))
    user_id = Column(Integer)  # User ID
    mobile = Column(Boolean)  # Is mobile client
    type = Column(SmallInteger)  # Client types
    locale = Column(String(2))  # Client locale
