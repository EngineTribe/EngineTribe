HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 25019  # Default port that SMM_WE uses
FLASK_DEBUG_MODE = True  # Whether to enable Flask's debug mode
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


ENGINE_BOT_WEBHOOK_URL = 'http://bot.enginetribe.gq/enginetribe'
