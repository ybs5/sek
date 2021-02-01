import json
import re
from urllib.parse import urlencode

import requests
from scrapy.http.response.html import HtmlResponse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from conf.chrome import PROXY, YANDEX_CONF
from engines.base import BaseEngine
from utils.logger import logger


class Yandex(BaseEngine):
    def __init__(self, engine_name='yandex', keyword='印度', search_type='text', since='', until=''):
        super(Yandex, self).__init__(index_url='',
                                     engine_name=engine_name,
                                     keyword=keyword,
                                     search_type=search_type,
                                     since=since,
                                     until=until)

    def get_text(self):
        """
        需要在yandex配置界面绑定ip白名单，否则获取不到数据
        配置地址：https://xml.yandex.com/settings/
        """
        logger.info(f'【yandex】 {self.keyword} preparing...')
        for i in range(10):
            try:
                self._get_text(i)
                logger.info(f'【yandex】page {i + 1} ({self.keyword}) done...')
            except Exception as e:  # noqa
                logger.error(f'【yandex】page {i + 1} ({self.keyword}) error, reason={e}. please check...')
        logger.info(f'【yandex】 {self.keyword} completed...')

    def _get_text(self, page_index):
        params = {
            'l10n': 'en',
            'user': YANDEX_CONF['user'],
            'key': YANDEX_CONF['key'],
            'query': f'{self.keyword}',
            'page': f'{page_index}',
            'groupby': 'attr="".mode=flat.groups-on-page=100.docs-in-group=1'
        }
        q_str = urlencode(params)
        url = f'https://yandex.com/search/xml?{q_str}'
        response = requests.get(url, proxies={'https': f'http://{PROXY}'}, timeout=15)

        resp = HtmlResponse(url=url, body=response.text, encoding='utf-8')
        data_list = []
        for el in resp.css('group'):
            publish_time = el.css('modtime::text').get(default='')
            item = json.dumps({
                'url': el.css('url::text').get(),
                'title': ''.join(el.css('title::text, title *::text').extract()),
                'desc': ''.join(el.css('passages::text, passages *::text').extract()),
                'publish_time': self._get_time(publish_time)
            })
            data_list.append(item)

        page = page_index + 1
        self.redis_cli.push_page_data(data_list, page=page)
        self.sleep_by_random(page)

    @staticmethod
    def _get_time(t):
        if not re.match(r'\d{8}T\d{6}', t): return ''
        return f'{t[:4]}-{t[4:6]}-{t[6:8]} {t[9:11]}:{t[11:13]}:{t[13:15]}'

    def get_pic(self, fpath, hash_val, ex):
        self.index_url = 'https://yandex.com/images/'
        self.search_type = 'pic'
        results = []
        with self:
            self.driver.find_element_by_css_selector('button[aria-label="Image search"]').click()
            self.driver.find_element_by_css_selector('.cbir-panel__file-input').send_keys(fpath)

            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "other-sites__head")))
            resp = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
            for el in resp.css('ul.other-sites__container li'):
                results.append({
                    'pic_url': el.css('a.other-sites__preview-link::attr(href)').get(),
                    'title': el.css('.other-sites__snippet-title a::text').get(),
                    'detail_url': el.css('.other-sites__snippet-site a::attr(href)').get(),
                    'website': el.css('.other-sites__snippet-site a::text').get(),
                    'desc': el.css('.other-sites__snippet-desc::text').get(default='')
                })
        if results:
            self.redis_cli.con.set(hash_val, json.dumps(results), ex=ex)
        return results

    def get_video(self):
        ...


if __name__ == '__main__':
    yandex = Yandex(keyword='秦始皇')
    with yandex:
        yandex.get_text()
    # yandex.get_pic()
