import requests
from urllib.parse import quote


class StorageAdapterOneDriveCF:
    def __init__(self, url: str, auth_key: str, proxied: bool):
        self.url = url
        self.auth_key = auth_key
        self.proxied = proxied
        self.type = 'onedrive-cf'

    def upload_file(self, level_name: str, level_data: str, level_id: str):
        try:
            response = requests.post(url=self.url, data=level_data,
                                     params={'upload': quote(level_name + ' ' + level_id + '.swe'),
                                             'key': self.auth_key})
        except Exception as e:
            return ConnectionError
        if response.text != '':
            return response.text
        else:
            return ConnectionError

    def generate_url(self, name: str, level_id: str):
        if self.proxied:
            return self.url + quote(name + ' ' + level_id) + '.swe' + '?proxied'
        else:
            return self.url + quote(name + ' ' + level_id) + '.swe'

    def generate_download_url(self, name: str, level_id: str):
        if self.proxied:
            return self.url + quote(name + ' ' + level_id) + '.swe' + '?raw&proxied'
        else:
            return self.url + quote(name + ' ' + level_id) + '.swe' + '?raw'

    def delete_level(self, name: str, level_id: str):
        print(f'Delete level {name} {level_id}: stubbed')
        return
