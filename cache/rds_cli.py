import json
import redis
from conf.conf import REDIS_HOST, REDIS_DB, REDIS_PORT


class RedisCli:

    def __init__(self, engine_name='google', keyword='', type_='text', since='', until=''):
        self.con = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_timeout=5
        )

        self.engine_name = engine_name
        self.keyword = keyword
        self._p1_key = f'SEK:::{self.keyword}:::{type_}:::{since}-{until}:::p1_process'
        self._data_key = f'SEK:::{engine_name}:::{keyword}:::{since}-{until}:::data'
        self._new_keyword = f'SEK:::{self.keyword}:::{type_}:::{since}-{until}:::new_keyword'

    def set_lock(self):
        self.con.set(self._new_keyword, 1)
        self.con.expire(self._new_keyword, 60)

    def is_locking(self):
        return self.con.exists(self._new_keyword)

    def del_lock(self):
        self.con.delete(self._new_keyword)

    def ajax_p1_loaded(self):
        key = self._p1_key
        self.con.sadd(key, self.engine_name)
        self.con.expire(key, 24 * 60 * 60)

    def get_p1_loaded_engines(self):
        return self.con.smembers(self._p1_key)

    def get_page_data(self, page_no=1, page_size=10):
        page_data = self.con.lrange(self._data_key, (page_no - 1) * page_size, page_no * page_size)
        return list(map(json.loads, page_data))

    def get_total(self):
        page_data = self.con.lrange(self._data_key, 0, 10)
        if not page_data:
            return 0

        total = self.con.llen(self._data_key)
        if total > 100:
            total = 100
        elif total <= 20:
            total = 20
        return total

    def push_page_data(self, data, page=1):
        if not data: return  # noqa
        if page == 1:
            self.ajax_p1_loaded()

        name = self._data_key
        self.con.rpush(name, *data)
        self.con.expire(name, 24 * 60 * 60)


if __name__ == '__main__':
    cli = RedisCli()
