HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 25019  # Default port that SMM_WE uses
API_KEY = "enginetribe"  # Engine-bot 's API key
ROWS_PERPAGE = 5  # Levels per page
UPLOAD_LIMIT = 25  # Max levels per account

DATABASE_ADAPTER = 'mysql'  # Database adapter to use, mysql, postgres and sqlite is supported
DATABASE_HOST = 'localhost'  # Database host (or file name when using sqlite)
DATABASE_PORT = 3306  # Database port
DATABASE_USER = 'enginetribe'  # Database user (not UNIX user)
DATABASE_PASS = 'enginetribe'  # Database password (not UNIX password)
DATABASE_NAME = 'enginetribe'  # Database name

STORAGE_ADAPTER = 'onedrive-cf'  # Storage adapter to use, only onedrive-cf is supported now
# onedrive-cf: https://github.com/spencerwooo/onedrive-cf-index
STORAGE_URL = 'https://storage.enginetribe.gq/'  # Storage url (with path)
STORAGE_AUTH_KEY = 'enginetribesA7EKiqBxY6QeH'  # Storage auth key
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN, onedrive-cf only

ENABLE_ENGINE_BOT_WEBHOOK = False
ENGINE_BOT_WEBHOOK_URLS = ['http://bot.enginetribe.gq/enginetribe']

ENABLE_DISCORD_WEBHOOK = True
DISCORD_WEBHOOK_URL = 'WEBHOOK_URL'
DISCORD_AVATAR_URL = 'https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine-bot.png'

OFFENSIVE_WORDS_FILTER = True
OFFENSIVE_WORDS_LIST = [
    'https://raw.githubusercontent.com/coffee-and-fun/google-profanity-words/main/data/list.txt']
OFFENSIVE_WORDS_LIST_CN_ONLY = [
    '']
