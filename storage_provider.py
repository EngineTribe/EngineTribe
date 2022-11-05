from urllib.parse import quote

import aiohttp
from io import BytesIO
from time import time
from hashlib import md5


class StorageProviderOneDriveCF:
    def __init__(self, url: str, auth_key: str, proxied: bool):
        self.url = url
        self.auth_key = auth_key
        self.proxied = proxied
        self.type = "onedrive-cf"

    # noinspection PyBroadException
    async def upload_file(self, level_data: str, level_id: str):
        try:
            async with aiohttp.request(
                    method="POST",
                    url=self.url,
                    data=level_data,
                    params={"upload": quote(level_id + ".swe"), "key": self.auth_key},
            ) as r:
                if (t := await r.text()) != "":
                    return t
                else:
                    return ConnectionError
        except Exception:
            return ConnectionError

    def generate_url(self, level_id: str):
        if self.proxied:
            return self.url + level_id + ".swe?proxied"
        else:
            return self.url + level_id + ".swe"

    def generate_download_url(self, level_id: str):
        if self.proxied:
            return self.url + level_id + ".swe?raw&proxied"
        else:
            return self.url + level_id + ".swe?raw"

    @staticmethod
    def delete_level(name: str, level_id: str):
        print(f"Delete level {name} {level_id}: stubbed")
        return


class StorageProviderOneManager:
    def __init__(self, url: str, admin_password: str):  # Proxied not supported
        self.url = url
        self.admin_password = admin_password
        self.type = "onemanager"

    # noinspection PyBroadException
    async def upload_file(self, level_data: str, level_id: str):
        print('start uploading')
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
        print(f"Delete level {name} {level_id}: stubbed")
        return

    @staticmethod
    def admin_password_to_cookie(admin_password: str) -> str:
        def md5sum(input_string: str) -> str:
            return md5(input_string.encode()).hexdigest()

        # function adminpass2cookie($name, $pass, $timestamp)
        # {return md5($name . ':' . md5($pass) . '@' . $timestamp) . "(" . $timestamp . ")";}

        timestamp = int(time()) + 604800  # $timestamp = time()+7*24*60*60;
        return md5sum(f'admin:{md5sum(admin_password)}@{timestamp}') + f'({timestamp})'
