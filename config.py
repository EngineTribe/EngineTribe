HOST = '0.0.0.0'  # Engine Tribe Central Server
PORT = 25019  # Default port that SMM_WE uses

DB_TYPE = 'mysql'  # Only MySQL is supported now
DB_HOST = 'localhost'  # MySQL host
DB_PORT = 3306  # MySQL port
DB_USER = 'enginetribe'  # MySQL user (not UNIX user)
DB_PASS = 'enginetribe'  # MySQL password (not UNIX password)
DB_NAME = 'enginetribe'  # MySQL database name

STORAGE_BACKEND = 'onedrive-cf-index'  # Only onedrive-cf-index is supported now
# https://github.com/spencerwooo/onedrive-cf-index
STORAGE_URL = 'https://enginetribe-central.sydzy.workers.dev/'  # onedrive-cf-index instance url with path
STORAGE_AUTH_KEY = 'enginetribesA7EKiqBxY6QeH'  # onedrive-cf-index Auth Key
STORAGE_PROXIED = True  # Proxy levels via CloudFlare CDN

ROWS_PERPAGE = 5  # Levels per page
