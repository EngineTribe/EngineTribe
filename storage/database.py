from database.db import Database
from database.db_access import DBAccessLayer
from base64 import b64decode, b64encode


class StorageProviderDatabase:
    def __init__(self, base_url: str, database: Database):
        self.base_url = base_url
        self.db = database
        self.type = "database"

    async def upload_file(self, level_data: str, level_id: str):
        async with self.db.async_session() as session:
            async with session.begin():
                dal = DBAccessLayer(session)
                await dal.add_level_data(
                    level_id=level_id,
                    level_data=b64decode(level_data[:-40].encode()).decode(),
                    level_checksum=level_data[-40:]
                )
                await dal.commit()

    def generate_url(self, level_id: str):
        return f'{self.base_url}stage/{level_id}/file'

    def generate_download_url(self, level_id: str):
        return self.generate_url(level_id=level_id)

    async def delete_level(self, level_id: str):
        async with self.db.async_session() as session:
            async with session.begin():
                dal = DBAccessLayer(session)
                await dal.delete_level_data(level_id=level_id)
                await dal.commit()
                print(f"Deleted level {level_id} from database")
                return

    async def dump_level_data(self, level_id: str) -> str | None:
        async with self.db.async_session() as session:
            async with session.begin():
                dal = DBAccessLayer(session)
                level = (await dal.dump_level_data(level_id=level_id))
                if level is not None:
                    if isinstance(level.level_data, str):
                        level_data = level.level_data.encode()
                    else:
                        level_data = level.level_data
                    return f'{b64encode(level_data).decode()}{level.level_checksum}'
                else:
                    return None
