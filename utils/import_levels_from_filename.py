import base64
import datetime
import sys

import rapidjson as json
import requests

sys.path.append('..')

import asyncio
from database import SMMWEDatabase
from config import *
from storage_provider import *

db = SMMWEDatabase()

if STORAGE_ADAPTER == 'onedrive-cf':
	storage = StorageProviderOneDriveCF(url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=False)

	environments = {"underground": "1", "castle": "2", "underwater": "3", "ghost": "4", "airship": "5", "forest": "6",
					"sky": "7", "desert": "8", "snow": "9", "fall": "10", "beach": "11"}


async def recover_level(level_id):
	try:
		db.Level.get(db.Level.level_id == level_id)
	except Exception:
		try:
			level_json = json.loads(
				base64.b64decode(requests.get(url=storage.generate_url(level_id)).text[:-40].encode()).decode())
		except Exception:
			level_json = json.loads(
				base64.b64decode(requests.get(url=storage.generate_url(level_id)).text[:-40].encode()).decode())
		level_metadata = level_json['MAIN']['AJUSTES'][0]

		if level_metadata['entorno'] in environments:
			environment = environments[level_metadata['entorno']]
		else:
			environment = "0"

		if 'etiqueta2' in level_metadata:
			tags2 = level_metadata['etiqueta2']
		else:
			tags2 = 15
		level = db.Level(name=f'{level_id} (Recovered)', likes=0, dislikes=0, intentos=0, muertes=0, victorias=0,
						 style=str(level_metadata['apariencia']), environment=environment,
						 tag_1=level_metadata['etiqueta1'], tag_2=tags2,
						 date=datetime.datetime.strptime(level_metadata['date'], '%d/%m/%Y'),
						 author=level_metadata['user'],
						 level_id=level_id, non_latin=False, record_user='', record=0, testing_client=False)
		level.save()
		print(f'Recovered {level_id} by {level_metadata["user"]}')
		return


async def main():
	level_ids = open('level_ids.txt').read().strip().split('\n')

	for level_id in level_ids:
		asyncio.create_task(recover_level(level_id))
	await asyncio.sleep(100000000000000000000000000000000000000)


asyncio.run(main())
