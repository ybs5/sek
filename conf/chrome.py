# selenium config
import os
import pathlib
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

PROXY = '127.0.0.1:1081'


def load_default_conf():
    options = webdriver.ChromeOptions()
    prefs = {
        "accept_languages": "en",
        "lang": "en_US.UTF-8",
        'intl.accept_languages': 'en,en_US'
    }

    options.add_experimental_option("prefs", prefs)
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = PROXY
    proxy.ssl_proxy = PROXY

    capabilities = webdriver.DesiredCapabilities.CHROME
    proxy.add_to_capabilities(capabilities)

    project_dir = pathlib.Path(__file__).parent.parent.absolute()
    execute_path = os.path.join(project_dir, 'bin', 'chromedriver')
    return {
        'capabilities': capabilities,
        'options': options,
        'executable_path': execute_path
    }
