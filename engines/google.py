import time

from scrapy.http.response.html import HtmlResponse
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from sek.conf.chrome import load_default_conf


def get_google_keywords(keyword):
    conf = load_default_conf()
    driver = webdriver.Chrome(
        executable_path=conf['executable_path'],
        options=conf['options'],
        desired_capabilities=conf['capabilities']
    )
    try:
        print(f'抓取关键词：{keyword}')
        driver.get(url='https://www.google.com/')
        input_box = driver.find_element_by_css_selector('input[title="Search"]')
        input_box.send_keys(keyword)
        input_box.send_keys(Keys.ENTER)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))
        for i in range(10):
            try:
                resp = HtmlResponse(url=driver.current_url, body=driver.page_source, encoding='utf-8')
                for el in resp.css('#search div.g'):
                    url = el.css('.rc > div:nth-child(1) a[ping]::attr(href)').get()
                    title = ''.join(el.css('.rc > div:nth-child(1) h3 *::text').extract())
                    desc = ''.join(el.css('.rc > div:nth-child(2) span *::text').extract())
                    print(url, '====', title, '      ', desc)

                driver.find_element_by_link_text("Next").click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))
                print(f'.............................{i + 1}.......................................')
                if i % 4 == 0:
                    time.sleep(6)
                else:
                    time.sleep(3)
            except:
                pass
    finally:
        print('准备退出')
        driver.close()


def parse(html):
    pass


if __name__ == '__main__':
    get_google_keywords('python')
