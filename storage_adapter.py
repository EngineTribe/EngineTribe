import requests
from urllib.parse import quote


class StorageAdapterOneDriveCF:
    def __init__(self, url: str, auth_key: str, proxied: bool):
        self.url = url
        self.auth_key = auth_key
        self.proxied = proxied
        self.type = 'onedrive'

    def upload_file(self, file_name: str, file_data: str):
        print(requests.post(url=self.url, params={'upload': quote(file_name), 'key': self.auth_key},
                            data=file_data))

    def convert_url(self, url: str):
        if self.proxied:
            return url + '?proxied'
        else:
            return url
