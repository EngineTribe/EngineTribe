from asyncio.queues import Queue as AsyncQueue
import aiohttp
import discord

from config import (
    ENGINE_BOT_WEBHOOK_URLS,
    DISCORD_WEBHOOK_URLS,
    DISCORD_AVATAR_URL,
    DISCORD_NICKNAME
)

engine_bot_push_queue: AsyncQueue = AsyncQueue()
discord_push_queue: AsyncQueue = AsyncQueue()

__all__ = [
    "push_to_engine_bot",
    "push_to_engine_bot_discord",
]


async def push_to_engine_bot(data: dict):
    # This function is used to push messages to general Engine Bots
    # (Not limited to QQ)
    # You can construct your own Engine Bot with this API for other IMs
    await engine_bot_push_queue.put(data)


async def push_to_engine_bot_discord(message: str):
    await discord_push_queue.put(message)


async def push_to_engine_bot_sub():
    while True:
        data = await engine_bot_push_queue.get()
        for webhook_url in ENGINE_BOT_WEBHOOK_URLS:
            async with aiohttp.request(
                    method="POST",
                    url=webhook_url,
                    json=data
            ) as response:
                pass


async def push_to_engine_bot_discord_sub():
    while True:
        message = await discord_push_queue.get()
        async with aiohttp.ClientSession() as session:
            for webhook_url in DISCORD_WEBHOOK_URLS:
                webhook = discord.Webhook.from_url(url=webhook_url, session=session)
                message: str = str(message)
                await webhook.send(str(message), username=DISCORD_NICKNAME, avatar_url=DISCORD_AVATAR_URL)
