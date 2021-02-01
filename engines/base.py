import random
import re
import time
from datetime import datetime, timedelta

from selenium import webdriver
from cache.rds_cli import RedisCli
from conf.chrome import load_default_conf
from utils.logger import logger


class BaseEngine:
    def __init__(self, index_url='', engine_name='google', keyword='印度', search_type='text', since='', until=''):
        self.index_url = index_url
        self.engine_name = engine_name
        self.keyword = keyword
        self.search_type = search_type
        self.since = since
        self.until = until

        self.conf = load_default_conf()
        self.driver = None
        self.redis_cli = RedisCli(engine_name, keyword, search_type, since, until)

    def __enter__(self):
        if self.engine_name == 'yandex' and self.search_type == 'text': return
        self.driver = webdriver.Chrome(
            executable_path=self.conf['executable_path'],
            options=self.conf['options'],
            desired_capabilities=self.conf['capabilities']
        )
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": self.conf['stealth_js']
        })
        self.driver.get(self.index_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.driver: return
        logger.info(f'browser exit. exc_type={exc_type}...')
        self.driver.quit()

    @staticmethod
    def sleep_by_random(cur_page=1):
        nonce = [2, 3, 2.4, 4, 2.8, 3, 3.5] if cur_page < 5 else [2, 2.5, 2.9, 3, 3.8, 4, 4.5, 5, 6]
        time.sleep(random.choice(nonce))

    @staticmethod
    def get_publish_time(desc):
        desc_txt = desc[:20]
        time_ = re.search(r'(\d+).*?ago\s', desc_txt)
        fmt = '%Y-%m-%d %H:%M:%S'
        if not time_:
            time_ = re.search(r'(\S+\s\d{1,2},\s\d{4})', desc_txt)
            if not time_:
                return ''
            publish_time = time_.group(1)
            timestamp = datetime.strptime(publish_time, '%b %d, %Y')
            return timestamp.strftime(fmt)

        num = int(time_.group(1))
        now = datetime.now()
        if 'min' in desc_txt:
            publish_time = now - timedelta(minutes=num)
        elif 'hour' in desc_txt:
            publish_time = now - timedelta(hours=num)
        elif 'day' in desc_txt:
            publish_time = now - timedelta(days=num)
        else:
            publish_time = now
        return publish_time.strftime(fmt)

    def get_text(self):
        raise NotImplementedError

    # def get_pic(self):
    #     raise NotImplementedError
    #
    # def get_video(self):
    #     raise NotImplementedError
