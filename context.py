from contextvars import ContextVar

from database import SMMWEDatabase

db = SMMWEDatabase()
db_ctx = ContextVar("db", default=SMMWEDatabase())
db_ctx.set(db)

connection_count = ContextVar("connection_count", default=0)
