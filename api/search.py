import json
import time
import multiprocessing

from fastapi import FastAPI

from cache.rds_cli import RedisCli
from engines.google import get_google_keywords


app = FastAPI()


@app.get("/api/v1/sek/search/")
async def read_root(q: str, page: int = 1):
    targets = [get_google_keywords, ]
    for target in targets:
        d = multiprocessing.Process(target=target, args=(1111,))
        d.daemon = True
        d.start()

    data = load_from_redis(q, page)
    if page == 1 and not any(data.values()):
        print('loading...,please wait')
        time.sleep(3)
        data = load_from_redis(q, page)

    return {
        'code': 0,
        'msg': '',
        'data': data
    }


def load_from_redis(keyword, page_no=1):
    engine_names = ('google', 'yandex', 'bing')
    search_result = {}
    for name in engine_names:
        cli = RedisCli(name, keyword)
        data = cli.get_page_data(page_no)
        search_result[name] = json.loads(data) if data else []

    return search_result
