HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 35000  # Default port that SMM_WE uses
API_KEY = "enginetribe"  # Engine-bot 's API key
ROWS_PERPAGE = 10  # Levels per page
UPLOAD_LIMIT = 25  # Max levels per account
BOOSTERS_EXTRA_LIMIT = 10  # Privileges of boosters
RECORD_CLEAR_USERS = True  # Record and display cleared users

DATABASE_ADAPTER = 'mysql'  # Database adapter to use, mysql, postgresql and sqlite is supported
DATABASE_HOST = 'localhost'  # Database host (or file name when using sqlite)
DATABASE_PORT = 3306  # Database port
DATABASE_USER = 'enginetribe'  # Database user (not UNIX user)
DATABASE_PASS = 'enginetribe'  # Database password (not UNIX password)
DATABASE_NAME = 'enginetribe'  # Database name
DATABASE_SSL = False  # Use SSL for database connection
DATABASE_DEBUG = False  # Log SQL connections to stdout

STORAGE_PROVIDER = 'database'  # Storage provider to use, onemanager, onedrive-cf and database are supported now
# - database: use database to store levels  (recommended)
# - onedrive-cf: https://github.com/spencerwooo/onedrive-cf-index
# - onemanager: https://github.com/qkqpttgf/OneManager-php
STORAGE_URL = 'http://enginetribe.gq:30000/'  # Storage url with '/'
STORAGE_AUTH_KEY = ''  # Storage auth key, onedrive-cf and onemanager only
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN, onedrive-cf only

ENABLE_ENGINE_BOT_WEBHOOK = False
ENABLE_ENGINE_BOT_COUNTER_WEBHOOK = False
ENABLE_ENGINE_BOT_ARRIVAL_WEBHOOK = False
ENGINE_BOT_WEBHOOK_URLS = ['http://bot.enginetribe.gq/enginetribe']

ENABLE_DISCORD_WEBHOOK = False
DISCORD_WEBHOOK_URLS = ['WEBHOOK_URL']
DISCORD_AVATAR_URL = 'https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine-bot.png'
