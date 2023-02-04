from database.db import Database
from database.db_access import DBAccessLayer
import aiohttp


class StorageProviderDiscord:

    def __init__(self, api_url: str, base_url: str, database: Database, attachment_channel: int):
        self.api_url = api_url
        self.base_url = base_url
        self.db = database
        self.attachment_channel = attachment_channel
        self.type = "discord"

    async def upload_file(
            self,
            level_data: str,
            level_id: str,
            level_db_id: int,
            level_name: str,
            level_author: str,
            level_author_im_id: int,
            level_tags: str
    ):
        async with aiohttp.request(
                method='POST',
                url=f'{self.api_url}/upload',
                json={
                    'level_data': level_data,
                    'level_id': level_id,
                    'level_name': level_name,
                    'level_author': level_author,
                    'level_author_im_id': level_author_im_id,
                    'level_tags': level_tags
                }
        ) as response:
            if response.status == 200:
                response_json = await response.json()
                if response_json['status'] == "success":
                    attachment_id = response_json['attachment_id']
                    print(attachment_id)
                    async with self.db.async_session() as session:
                        async with session.begin():
                            dal = DBAccessLayer(session)
                            await dal.add_level_discord(
                                level_db_id=level_db_id,
                                attachment_id=attachment_id,
                            )
                            await dal.commit()
                else:
                    raise ConnectionError
            else:
                raise ConnectionError

    async def generate_url(self, level_id: str, level_db_id: int, proxied: bool) -> str:
        if proxied:
            return f'{self.base_url}stage/{level_id}/file'
        else:
            async with self.db.async_session() as session:
                async with session.begin():
                    dal = DBAccessLayer(session)
                    level_discord = await dal.get_level_discord(level_db_id=level_db_id)
                    if level_discord is not None:
                        return f'https://cdn.discordapp.com/attachments/' \
                               f'{self.attachment_channel}/{level_discord.attachment_id}/{level_id}.swe'
                    else:
                        return ''

    async def generate_download_url(self, level_id: str, level_db_id: int, proxied: bool) -> str:
        return await self.generate_url(level_id=level_id, level_db_id=level_db_id, proxied=proxied)
