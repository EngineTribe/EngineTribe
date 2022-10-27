from contextvars import ContextVar

from config import STORAGE_URL, STORAGE_AUTH_KEY, STORAGE_PROXIED, STORAGE_PROVIDER
from database import SMMWEDatabase
from storage_provider import StorageProviderOneDriveCF

db = SMMWEDatabase()
db_ctx = ContextVar("db", default=db)
db_ctx.set(db)

connection_count = ContextVar("connection_count", default=0)

# Only onedrive-cf storage provider is supported now
if STORAGE_PROVIDER == "onedrive-cf":
    storage = StorageProviderOneDriveCF(
        url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED
    )
