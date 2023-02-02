#!/usr/bin/env python3

import datetime
import platform
from typing import Optional
import uvicorn
from fastapi import FastAPI, Form, Request, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from redis import asyncio as redis

from database.db_access import DBAccessLayer
import routers
from config import *
from models import ErrorMessage, ErrorMessageException
from common import *
from database.db import Database
from storage_provider import (
    StorageProviderOneDriveCF,
    StorageProviderOneManager,
    StorageProviderDatabase
)
from depends import (
    create_dal
)

app = FastAPI()

app.include_router(routers.stage.router)
app.include_router(routers.user.router)

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
            base_url=STORAGE_URL,
            database=app.state.db
        )
    }[STORAGE_PROVIDER]
    app.state.redis_1 = redis.Redis(
        connection_pool=redis.ConnectionPool(
            host=SESSION_REDIS_HOST,
            port=SESSION_REDIS_PORT,
            db=SESSION_REDIS_DB_1,
            password=SESSION_REDIS_PASS
        )
    )
    app.state.redis_2 = redis.Redis(
        connection_pool=redis.ConnectionPool(
            host=SESSION_REDIS_HOST,
            port=SESSION_REDIS_PORT,
            db=SESSION_REDIS_DB_2,
            password=SESSION_REDIS_PASS
        )
    )


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()


@app.get("/")
async def readme_handler() -> RedirectResponse:  # Redirect to Engine Tribe README
    return RedirectResponse("https://web.enginetribe.gq/index.html")


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


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, headers=[("Server", "EngineTribe")])
