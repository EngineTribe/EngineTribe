from loguru import logger

class StorageProviderDiscord:

    def __init__(self, api_url, base_url, database, attachment_channel):
        logger.error('Discord storage provider is deprecated. Use other storage providers instead.')
