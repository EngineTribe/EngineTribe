from contextvars import ContextVar

from database import SMMWEDatabase

db = SMMWEDatabase()
db_ctx = ContextVar("db", default=db)
db_ctx.set(db)

connection_count = ContextVar("connection_count", default=0)
