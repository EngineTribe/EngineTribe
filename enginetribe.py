#!/usr/bin/env python3

import datetime
import platform
from typing import Optional
import uvicorn
from fastapi import FastAPI, Form, Request, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis import asyncio as redis
import asyncio

from database.db_access import DBAccessLayer
import routers
from config import *
from models import ErrorMessage, ErrorMessageException
from common import *
import push
from database.db import Database
from storage.onedrive_cf import StorageProviderOneDriveCF
from storage.onemanager import StorageProviderOneManager
from storage.database import StorageProviderDatabase
from storage.discord import StorageProviderDiscord
from depends import (
    create_dal
)


async def connection_per_minute_record():
    await asyncio.sleep(60)
    app.state.connection_per_minute = app.state.connection_count
    app.state.connection_count = 0
    asyncio.create_task(connection_per_minute_record())


app = FastAPI()

app.include_router(routers.stage.router)
app.include_router(routers.user.router)
app.include_router(routers.client.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = datetime.datetime.now()


@app.on_event("startup")
async def startup_event():
    app.state.db = Database()
    await app.state.db.create_columns()
    app.state.connection_count = 0
    app.state.storage = {
        "onedrive-cf": StorageProviderOneDriveCF(
            url=STORAGE_URL, auth_key=STORAGE_AUTH_KEY, proxied=STORAGE_PROXIED
        ),
        "onemanager": StorageProviderOneManager(
            url=STORAGE_URL, admin_password=STORAGE_AUTH_KEY
        ),
        "database": StorageProviderDatabase(
            base_url=API_ROOT,
            database=app.state.db
        ),
        "discord": StorageProviderDiscord(
            api_url=STORAGE_URL,
            base_url=API_ROOT,
            database=app.state.db,
            attachment_channel=STORAGE_ATTACHMENT_CHANNEL_ID
        )
    }[STORAGE_PROVIDER]
    app.state.redis = redis.Redis(
        connection_pool=redis.ConnectionPool(
            host=SESSION_REDIS_HOST,
            port=SESSION_REDIS_PORT,
            db=SESSION_REDIS_DB,
            password=SESSION_REDIS_PASS
        )
    )
    app.state.connection_count = 0
    app.state.connection_per_minute = 0
    asyncio.create_task(connection_per_minute_record())
    asyncio.create_task(push.push_to_engine_bot_sub())
    asyncio.create_task(push.push_to_engine_bot_discord_sub())


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.flushdb()
    await app.state.redis.close()


@app.get("/")
async def readme_handler() -> RedirectResponse:  # Redirect to Engine Tribe README
    return RedirectResponse("https://www.enginetribe.gq/")


# get server status
@app.get("/server_stats")
async def server_stats(
        dal: DBAccessLayer = Depends(create_dal)
) -> dict:
    return {
        "os": platform.platform().replace('-', ' '),
        "python": platform.python_version(),
        "player_count": await dal.get_player_count(),
        "level_count": await dal.get_level_count(),
        "uptime": (datetime.datetime.now() - start_time).seconds,
        "connection_per_minute": app.state.connection_per_minute,
    }


@app.exception_handler(ErrorMessageException)
async def error_message_exception_handler(request: Request, exc: ErrorMessageException):
    return JSONResponse(
        status_code=200,
        content={
            "error_type": exc.error_type,
            "message": exc.message,
        },
    )


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def route_not_found_handler(request: Request, exc: ErrorMessageException):
    return JSONResponse(
        status_code=404,
        content={
            "error_type": "001",
            "message": "Route not found.",
        },
    )


def run():
    uvicorn.run(
        app=app,
        host=HOST,
        port=PORT,
        workers=WORKERS,
        headers=[
            ("Server", "EngineTribe"),
            ("X-Powered-By", "EngineTribe"),
        ]
    )


if __name__ == "__main__":
    run()
