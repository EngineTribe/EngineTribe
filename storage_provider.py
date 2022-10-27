from urllib.parse import quote

import aiohttp


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
