HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 25019  # Default port that SMM_WE uses
API_KEY = "enginetribe"  # Engine-bot 's API key

DB_TYPE = 'mysql'  # Database to use, mysql, postgres and sqlite is supported
DB_HOST = 'localhost'  # Database host (or file name when using sqlite)
DB_PORT = 3306  # Database port
DB_USER = 'enginetribe'  # Database user (not UNIX user)
DB_PASS = 'enginetribe'  # Database password (not UNIX password)
DB_NAME = 'enginetribe'  # Database name

STORAGE_ADAPTER = 'onedrive-cf'  # Storage adapter to use, only onedrive-cf is supported now
# onedrive-cf: https://github.com/spencerwooo/onedrive-cf-index
STORAGE_URL = 'https://enginetribe-central.sydzy.workers.dev/'  # Storage url (with path)
STORAGE_AUTH_KEY = 'enginetribesA7EKiqBxY6QeH'  # Storage auth key
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN, onedrive-cf only

ROWS_PERPAGE = 5  # Levels per page
