import json

from scrapy.http.response.html import HtmlResponse
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.errorhandler import ElementClickInterceptedException

from engines.base import BaseEngine
from utils.logger import logger


class Bing(BaseEngine):
    def __init__(self, engine_name='bing', keyword='印度', search_type='text', since='', until=''):
        super(Bing, self).__init__(index_url='https://www.bing.com/',
                                   engine_name=engine_name,
                                   keyword=keyword,
                                   search_type=search_type,
                                   since=since,
                                   until=until)

    def get_text(self):
        input_box = self.driver.find_element_by_css_selector('#sb_form_q')
        input_box.send_keys(self.keyword)
        input_box.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "sw_next")))
        # bing不支持按时间范围筛选, also see:
        # https://www.thinbug.com/q/11643567
        for i in range(10):
            try:
                logger.info(f'【bing】:{i + 1}')
                resp = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
                data_list = []
                for el in resp.css('#b_results li.b_algo'):
                    desc = ''.join(el.css('div.b_caption p::text,'
                                          'div.b_caption p *::text,'
                                          'div.rebateContainer::text,'
                                          'div.rebateContainer strong::text').extract())
                    item = json.dumps({
                        'url': el.css('h2 a[h]::attr(href)').get(),
                        'title': ''.join(el.css('h2 a[h]::text').extract()),
                        'desc': desc,
                        'publish_time': self.get_publish_time(desc)
                    }, ensure_ascii=False)
                    data_list.append(item)

                self.redis_cli.push_page_data(data_list, page=i + 1)
                try:
                    self.driver.find_element_by_css_selector('a[title="Next page"]').click()
                except ElementClickInterceptedException:
                    logger.info('【bing】 点击异常，准备重试...')
                    self.driver.find_element_by_css_selector(f'a[aria-label="Page {i + 2}"]').click()

                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sw_next")))
                self.sleep_by_random(i)
            except Exception as e:
                logger.info(f'【bing】 error,msg:{e}')

    def get_pic(self):
        ...

    def get_video(self):
        ...


if __name__ == '__main__':
    # get_bing_keywords('俄罗斯B3 -ad')
    bing = Bing(keyword='Anti-cow slaughter bill passed')
    with bing:
        bing.get_text()
