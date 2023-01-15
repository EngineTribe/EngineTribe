#!/usr/bin/env python3

import datetime
import platform
import threading
from math import ceil
from typing import Optional

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse

import context
import routers
from config import *
from dfa_filter import DFAFilter
from models import ErrorMessage, ErrorMessageException
from smmwe_lib import *

app = FastAPI()

app.include_router(routers.stage.router)
app.include_router(routers.user.router)

connection_per_minute = 0

start_time = datetime.datetime.now()

if OFFENSIVE_WORDS_FILTER:
    import requests

    # Load DFA filter
    dfa_filter = DFAFilter()
    wordlist = None
    for url in OFFENSIVE_WORDS_LIST:
        wordlist = requests.get(url=url).text.replace("\r", "").split("\n")
    for word in wordlist:
        if len(word) > 1 and len(word.encode("utf-8")) > 2:
            dfa_filter.add(word)
    for url in OFFENSIVE_WORDS_LIST_CN_ONLY:
        wordlist = requests.get(url=url).text.replace("\r", "").split("\n")
        for word in wordlist:
            if len(re.findall(re.compile(r"[A-Za-z]", re.S), word)) == 0:
                if len(word) > 1 and len(word.encode("utf-8")) > 2:
                    dfa_filter.add(word)


@app.on_event("startup")
async def startup_event():
    await context.db.create_columns()


@app.get("/")
async def readme_handler() -> RedirectResponse:  # Redirect to Engine Tribe README
    return RedirectResponse("https://web.enginetribe.gq/index.html")


# get server status
@app.get("/server_stats")
async def server_stats() -> dict:
    return {
        "os": platform.platform().replace('-', ' '),
        "python": platform.python_version(),
        "player_count": context.db.User.select().count(),
        "level_count": context.db.Level.select().count(),
        "uptime": datetime.datetime.now() - start_time,
        "connection_per_minute": connection_per_minute,
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


def timer_function():
    global connection_per_minute
    connection_per_minute = context.connection_count
    context.connection_count = 0
    threading.Timer(60, timer_function).start()


if __name__ == "__main__":
    threading.Timer(1, timer_function).start()
    uvicorn.run(app, host=HOST, port=PORT, headers=[("Server", "EngineTribe")])
