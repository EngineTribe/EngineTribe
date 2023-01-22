from config import STORAGE_URL, STORAGE_AUTH_KEY, STORAGE_PROXIED, STORAGE_PROVIDER
from database.db import Database
from storage_provider import StorageProviderOneDriveCF, StorageProviderOneManager, StorageProviderDatabase

db: Database = Database()

connection_count: int = 0

match STORAGE_PROVIDER:
    case "onedrive-cf":
        storage = StorageProviderOneDriveCF(
            url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED
        )
    case "onemanager":
        storage = StorageProviderOneManager(
            url=STORAGE_URL, admin_password=STORAGE_AUTH_KEY
        )
    case "database":
        storage = StorageProviderDatabase(
            base_url=STORAGE_URL,
            database=db
        )
