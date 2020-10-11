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
        # self.process_name = f'{engine_name}:::{keyword}:::process'
        self.data_name = f'{engine_name}:::{keyword}:::data'

    # @property
    # def parsed_total_page(self):
    #     key = self.process_name
    #     return self.con.get(key)
    #
    # def recode_process(self):
    #     key = self.process_name
    #     self.con.incr(key)

    def get_page_data(self, page_no=1, page_size=10):
        self.con.lrange(self.data_name, (page_no - 1) * page_size, page_size)

    def push_page_data(self, data):
        self.con.lpush(self.data_name, *data)


if __name__ == '__main__':
    cli = RedisCli()
