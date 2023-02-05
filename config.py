import os

import yaml

config_path = os.getenv("CONFIG_PATH", "config.yml")

_config = yaml.safe_load(open(config_path, "r"))

HOST = _config["enginetribe"]["host"]
PORT = _config["enginetribe"]["port"]
API_ROOT = _config["enginetribe"]["api_root"]
VERIFY_USER_AGENT = _config["enginetribe"]["verify_user_agent"]
API_KEY = _config["enginetribe"]["api_key"]
ROWS_PERPAGE = _config["enginetribe"]["rows_perpage"]
UPLOAD_LIMIT = _config["enginetribe"]["upload_limit"]
BOOSTERS_EXTRA_LIMIT = _config["enginetribe"]["booster_extra_limit"]
RECORD_CLEAR_USERS = _config["enginetribe"]["record_clear_users"]

DATABASE_ADAPTER = _config['database']['adapter']
DATABASE_HOST = _config['database']['host']
DATABASE_PORT = _config['database']['port']
DATABASE_USER = _config['database']['user']
DATABASE_PASS = _config['database']['password']
DATABASE_NAME = _config['database']['database']
DATABASE_SSL = _config['database']['ssl']
DATABASE_DEBUG = _config['database']['debug']

SESSION_REDIS_HOST = _config['redis']['host']
SESSION_REDIS_PORT = _config['redis']['port']
SESSION_REDIS_DB = _config['redis']['database']
SESSION_REDIS_PASS = _config['redis']['password']

STORAGE_PROVIDER = _config['storage']['provider']
STORAGE_URL = _config['storage']['url']
STORAGE_AUTH_KEY = _config['storage']['auth_key']
STORAGE_PROXIED = _config['storage']['proxied']
STORAGE_ATTACHMENT_CHANNEL_ID = _config['storage']['attachment_channel_id']

ENABLE_ENGINE_BOT_WEBHOOK = _config['push']['engine_bot']['enabled']
ENABLE_ENGINE_BOT_COUNTER_WEBHOOK = _config['push']['engine_bot']['enable_counter']
ENABLE_ENGINE_BOT_ARRIVAL_WEBHOOK = _config['push']['engine_bot']['enable_new_arrival']
ENGINE_BOT_WEBHOOK_URLS = _config['push']['engine_bot']['urls']

ENABLE_DISCORD_WEBHOOK = _config['push']['discord']['enabled']
ENABLE_DISCORD_ARRIVAL_WEBHOOK = _config['push']['discord']['enable_new_arrival']
DISCORD_WEBHOOK_URLS = _config['push']['discord']['urls']
DISCORD_AVATAR_URL = _config['push']['discord']['avatar']
