import time
from datetime import datetime, timedelta, date
import redis


class RedisCli:

    def __init__(self, engine_name='google', keyword=''):
        self.con = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            socket_timeout=5
        )
        self.engine_name = engine_name
        self.keyword = keyword

    @property
    def parsed_total_page(self):
        key = f'{self.engine_name}:::{self.keyword}:::process'
        return self.con.get(key)


if __name__ == '__main__':
    cli = RedisCli()
