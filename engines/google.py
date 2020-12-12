import json
import time

from scrapy.http.response.html import HtmlResponse
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from engines.base import BaseEngine
from utils.logger import logger


class Google(BaseEngine):
    def __init__(self, engine_name='google', keyword='印度', search_type='text', since='', until=''):
        super(Google, self).__init__(index_url='https://www.google.com/ncr',
                                     engine_name=engine_name,
                                     keyword=keyword,
                                     search_type=search_type,
                                     since=since,
                                     until=until)

    def get_text(self):
        input_box = self.driver.find_element_by_css_selector('input[title="Search"], input[title]')
        input_box.send_keys(self.keyword)
        input_box.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))
        if self.since or self.until:
            self.driver.find_element_by_id('hdtb-tls').click()
            time.sleep(0.5)
            bt2 = self.driver.find_element_by_css_selector('.hdtb-mn-hd .mn-hd-txt')
            self.driver.execute_script("arguments[0].click();", bt2)
            self.driver.find_element_by_css_selector('#lb g-menu g-menu-item:nth-last-child(1)').click()
            time.sleep(0.3)
            form = self.driver.find_element_by_css_selector('form[action="/search"]:not([data-submitfalse])')

            if self.since:
                since = self.custom_date(self.since)
                form.find_element_by_css_selector('input[jsaction][autocomplete]').send_keys(since)

            if self.until:
                until = self.custom_date(self.until)
                form.find_elements_by_css_selector('input[jsaction][autocomplete]')[-1].send_keys(until)

            form.find_element_by_css_selector('g-button').click()
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))

        for i in range(10):
            try:
                logger.info(f'【google】: page {i + 1}')
                resp = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')

                data_list = []
                for el in resp.css('#search div[class="g"]'):
                    title = ''.join(el.css('.rc > div:nth-child(1) h3 *::text').extract())
                    url = el.css('.rc > div:nth-child(1) a::attr(href)').get()
                    desc = ''.join(el.css('.rc > div:nth-child(2) span *:not([class="f"])::text').extract())
                    time_info = el.css('.rc > div:nth-child(2) span *[class="f"]::text').get(default='')
                    item = json.dumps({
                        'url': url,
                        'title': title,
                        'desc': desc,
                        'publish_time': self.get_publish_time(time_info)
                    }, ensure_ascii=False)
                    if not title.strip() or not url: continue  # noqa
                    data_list.append(item)

                self.redis_cli.push_page_data(data_list, page=i + 1)
                self.driver.find_element_by_link_text("Next").click()
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))
                self.sleep_by_random(i)
            except Exception as e:
                logger.error(f'parse 【google】:{i + 1} error, reason={e}')

    def get_pic(self):
        ...

    def get_video(self):
        ...

    @staticmethod
    def custom_date(datestr):
        year, month, day = datestr[0:4], int(datestr[4:6]), int(datestr[6:-1])
        return f'{month}/{day}/{year}'


if __name__ == '__main__':
    # google = Google(index_url='https://www.google.com/ncr')
    # txt = '22 hours ago — Carsome, which bills itself as Southeast'
    google = Google(since='20170812', keyword='C++')
    # res = google.get_publish_time(txt)
    # print(res)
    with google:
        google.get_text()
    # get_google_keywords('python')
