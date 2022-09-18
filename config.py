HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 25019  # Default port that SMM_WE uses
API_KEY = "enginetribe"  # Engine-bot 's API key

DB_TYPE = 'mysql'  # Database to use, mysql, postgres and sqlite is supported
DB_HOST = 'localhost'  # Database host (or file name when using sqlite)
DB_PORT = 3306  # Database port
DB_USER = 'enginetribe'  # Database user (not UNIX user)
DB_PASS = 'enginetribe'  # Database password (not UNIX password)
DB_NAME = 'enginetribe'  # Database name

STORAGE_BACKEND = 'onedrive-cf-index'  # Only onedrive-cf-index is supported now
# https://github.com/spencerwooo/onedrive-cf-index
STORAGE_URL = 'https://enginetribe-central.sydzy.workers.dev/'  # onedrive-cf-index instance url with path
STORAGE_AUTH_KEY = 'enginetribesA7EKiqBxY6QeH'  # onedrive-cf-index Auth Key
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN

ROWS_PERPAGE = 5  # Levels per page
