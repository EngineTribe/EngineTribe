import aiohttp
from hashlib import md5
from io import BytesIO
from time import time
from loguru import logger


class StorageProviderOneManager:
    def __init__(self, url: str, admin_password: str):  # Proxied not supported
        self.url = url
        self.admin_password = admin_password
        self.type = "onemanager"

    # noinspection PyBroadException
    async def upload_file(self, level_data: str, level_id: str):
        logger.info(f'start uploading level {level_id}...')
        postfields = aiohttp.FormData()
        postfields.add_field(name='file1',
                             value=BytesIO(bytes(level_data, 'ascii')),
                             content_type='text/plain',
                             filename=level_id + ".swe"
                             )

        try:
            async with aiohttp.request(
                    method="POST",
                    url=self.url + '?action=upsmallfile',
                    data=postfields,
                    headers={'Cookie': 'admin=' + self.admin_password_to_cookie(self.admin_password)}
            ) as response:
                if (t := await response.text())[1] != "{":
                    return t
                else:
                    return ConnectionError
        except Exception:
            return ConnectionError

    def generate_url(self, level_id: str):
        return self.url + level_id + ".swe"

    def generate_download_url(self, level_id: str):
        return self.url + level_id + ".swe"

    @staticmethod
    def delete_level(name: str, level_id: str):
        logger.info(f"Delete level {name} {level_id}: stubbed")
        return

    @staticmethod
    def admin_password_to_cookie(admin_password: str) -> str:
        def md5sum(input_string: str) -> str:
            return md5(input_string.encode()).hexdigest()

        # function adminpass2cookie($name, $pass, $timestamp)
        # {return md5($name . ':' . md5($pass) . '@' . $timestamp) . "(" . $timestamp . ")";}

        timestamp = int(time()) + 604800  # $timestamp = time()+7*24*60*60;
        return md5sum(f'admin:{md5sum(admin_password)}@{timestamp}') + f'({timestamp})'
