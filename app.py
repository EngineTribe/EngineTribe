import datetime
import platform
import threading
from math import ceil
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse

import context
import routers
from config import *
from dfa_filter import DFAFilter
from models import ErrorMessage
from smmwe_lib import *

app = FastAPI()

# init in context.py
db = context.db_ctx.get()

app.include_router(routers.stage.router)
app.include_router(routers.user.router)

connection_count = context.connection_count
connection_per_minute = 0

start_time = datetime.datetime.now()

# auto create table
db.Level.create_table()
db.User.create_table()
db.Stats.create_table()

if OFFENSIVE_WORDS_FILTER:
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


@app.get("/")
async def readme_handler():  # Redirect to Engine Tribe README
    return RedirectResponse("https://web.enginetribe.gq/index.html")


# get server status
@app.get("/server_stats")
async def server_stats():
    global connection_per_minute, start_time
    return {
        "os": f"{platform.platform()}",
        "python": platform.python_version(),
        "player_count": db.User.select().count(),
        "level_count": db.Level.select().count(),
        "uptime": datetime.datetime.now() - start_time,
        "connection_per_minute": connection_per_minute,
    }


def timer_function():
    global connection_per_minute
    connection_per_minute = connection_count.get()
    connection_count.set(0)
    threading.Timer(60, timer_function).start()


if __name__ == "__main__":
    threading.Timer(1, timer_function).start()
    uvicorn.run(app, host=HOST, port=PORT)
