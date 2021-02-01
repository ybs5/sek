import hashlib
import json
import multiprocessing
import pathlib
import tempfile
import time
from enum import Enum

from fastapi import FastAPI, Depends, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from cache.rds_cli import RedisCli
from engines import Google, Yandex, Bing
from utils.logger import logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等。
    allow_headers=["*"]  # 允许跨域的headers，可以用来鉴别来源等作用。
)


def response_fmt(data):
    return {
        'code': 0,
        'msg': '',
        'data': data
    }


@app.exception_handler(Exception)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(content={
        'code': -1,
        'msg': f'处理失败，原因:{str(exc)}',
    },
        status_code=500)


class Engines(Enum):
    _ = ''
    google = 'google'
    yandex = 'yandex'
    bing = 'bing'


class ReqSearch(BaseModel):
    q: str = Field('印度', description='搜索关键词', min_length=1)
    page: int = Field(1, gt=0, lt=11)
    engine: Engines = Field('')
    since: str = Field('', regex=r'20\d{2}(0[1-9]|1[0-2])|')
    until: str = Field('', regex=r'20\d{2}(0[1-9]|1[0-2])|')
    sort_by_time: int = Field(0, description='是否按照时间排序，默认否表示按照搜索引擎结果排序')

    class Config:
        schema_extra = {
            'examples': [
                {
                    'q': '印度',
                    'page': 1,
                    'engine': '',
                    'since': '',
                    'until': '',
                    'sort_by_time': 0
                }
            ]
        }

    @validator("until", always=True)
    def validate_date(cls, value, values):
        since = values['since']
        if since:
            if value <= since:
                raise ValueError(f'until({value}) must greater than since({since})')


@app.get("/api/v1/sek/search/")
def search_keyword(req: ReqSearch = Depends()):
    engines_info = {
        'google': Google(keyword=req.q, since=req.since, until=req.until),
        'bing': Bing(keyword=req.q, since=req.since, until=req.until),
        'yandex': Yandex(keyword=req.q, since=req.since, until=req.until)
    }

    name = req.engine.value
    instance = engines_info.get(name)
    if instance:
        engines = [(name, instance)]
        engine_names = (name,)
    else:
        engines = list(engines_info.items())
        engine_names = list(engines_info.keys())

    keywords_lock = SameConditionLock(req, engine_names=engine_names)
    with keywords_lock:
        data = load_result(req, engine_names)

    fetched = [bool(data[name]['total']) for name in data]
    if req.page == 1 and not any(fetched):
        keywords_lock.lock()

        def search(engine_instance):
            with engine_instance:
                engine_instance.get_text()

        exists_engines = [k for k in data.keys() if data[k]['details']]
        for name, _instance in engines:
            if name in exists_engines: continue
            d = multiprocessing.Process(target=search, args=(_instance,))
            d.daemon = True
            d.start()
        keywords_lock.wait_release(data.keys())
        data = load_result(req, engine_names)

    return response_fmt(data)


def load_result(req: ReqSearch, engine_names=('google', 'bing', 'yandex')):
    search_result = {}
    for name in engine_names:
        cli = RedisCli(name, keyword=req.q, since=req.since, until=req.until)
        data = cli.get_page_data(req.page)
        search_result[name] = {
            'details': data,
            'total': cli.get_total()
        }

    return search_result


class SameConditionLock:
    def __init__(self,
                 req: ReqSearch,
                 type_='text',
                 engine_names=('google', 'bing', 'yandex')):
        self.req = req
        self.type_ = type_
        self.engine_names = engine_names
        self.begin_time = None
        self.cli = RedisCli(keyword=self.req.q, since=self.req.since, until=self.req.until)

    def __enter__(self):
        if self.req.page != 1: return
        self.block(self.engine_names)

    def block(self, engine_names):
        if not self.cli.is_locking(): return
        i, wait_max_cnt = 0, 30
        while set(engine_names) != set(self.cli.get_p1_loaded_engines()):
            i += 1
            if i > wait_max_cnt:
                logger.error(f'Not found search engine result, please check...')
                break
            time.sleep(0.5)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f'lock is error...{exc_type}')

    def lock(self):
        self.begin_time = time.time()
        self.cli.set_lock()

    def wait_release(self, engine_names):
        self.block(engine_names)
        cost = int(time.time() - self.begin_time)
        self.cli.del_lock()
        logger.info(f'耗时：{cost}S')


@app.post("/api/v1/yandex/pic/search")
def search_pic(pic: UploadFile = File(...)):
    """YANDEX 以图搜图"""
    suffix = pathlib.Path(pic.filename).suffix
    logger.info(f'Received {pic.filename}...')
    binary_content = pic.file.read()
    sha1 = hashlib.sha1()
    sha1.update(binary_content)
    hash_val = sha1.hexdigest()

    rds_cli = RedisCli()
    results = rds_cli.con.get(hash_val)
    if results:
        data = json.loads(results)
        return response_fmt(data)

    with tempfile.NamedTemporaryFile(suffix=suffix) as fp:
        fp.write(binary_content)
        yandex = Yandex(search_type='pic')
        results = yandex.get_pic(fp.name, hash_val, ex=12 * 60 * 60)
        logger.info(f'deleting {fp.name}...')
    return response_fmt(results)


# @app.get("/api/v1/sek/video/")
# def search_video():
#     ...


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=9600)
