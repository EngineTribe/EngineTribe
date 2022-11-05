HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 80  # Default port that SMM_WE uses
API_KEY = "enginetribe"  # Engine-bot 's API key
ROWS_PERPAGE = 5  # Levels per page
UPLOAD_LIMIT = 25  # Max levels per account
BOOSTERS_EXTRA_LIMIT = 10  # Privileges of boosters

DATABASE_ADAPTER = 'mysql'  # Database adapter to use, mysql, postgres and sqlite is supported
DATABASE_HOST = 'localhost'  # Database host (or file name when using sqlite)
DATABASE_PORT = 3306  # Database port
DATABASE_USER = 'enginetribe'  # Database user (not UNIX user)
DATABASE_PASS = 'enginetribe'  # Database password (not UNIX password)
DATABASE_NAME = 'enginetribe'  # Database name

STORAGE_PROVIDER = 'onemanager'  # Storage provider to use, onemanager and onedrive-cf are supported now
# onedrive-cf: https://github.com/spencerwooo/onedrive-cf-index
# onemanager: https://github.com/qkqpttgf/OneManager-php
STORAGE_URL = 'http://storage-v2.enginetribe.gq:8086/'  # Storage url (with path)
STORAGE_AUTH_KEY = 'qoKJsiEt8bgBBj8r5X3C4y'  # Storage auth key
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN, onedrive-cf only

ENABLE_ENGINE_BOT_WEBHOOK = False
ENABLE_ENGINE_BOT_COUNTER_WEBHOOK = False
ENGINE_BOT_WEBHOOK_URLS = ['http://bot.enginetribe.gq/enginetribe']

ENABLE_DISCORD_WEBHOOK = False
DISCORD_WEBHOOK_URL = 'WEBHOOK_URL'
DISCORD_AVATAR_URL = 'https://raw.githubusercontent.com/EngineTribe/EngineBotDiscord/main/assets/engine-bot.png'

OFFENSIVE_WORDS_FILTER = False
OFFENSIVE_WORDS_LIST = [
            'https://raw.githubusercontent.com/coffee-and-fun/google-profanity-words/main/data/list.txt',
                    'https://raw.githubusercontent.com/fighting41love/funNLP/5da5ac5a5e665902d538ff9faf461186356afac4/data/%E6%95%8F%E6%84%9F%E8%AF%8D%E5%BA%93/%E6%94%BF%E6%B2%BB%E7%B1%BB.txt']
OFFENSIVE_WORDS_LIST_CN_ONLY = ['https://raw.githubusercontent.com/fighting41love/funNLP/5da5ac5a5e665902d538ff9faf461186356afac4/data/%E6%95%8F%E6%84%9F%E8%AF%8D%E5%BA%93/%E6%95%8F%E6%84%9F%E8%AF%8D.txt']