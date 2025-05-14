"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
# from seleniumwire import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import seleniumwire.undetected_chromedriver as uc
from seleniumwire.utils import decode
from selenium.webdriver.chrome.options import Options
import os
import logging


class SeleniumClient:
    def __init__(self):
        # self.driver = self.get_chrome_driver()
        pass

    def get_chrome_driver(self) -> None:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """

        chrome_options = uc.ChromeOptions()
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--ignore-certificate-errors")
        # chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"

        driver = uc.Chrome(
            desired_capabilities=caps,
            headless=True,
            options=chrome_options,
            seleniumwire_options={"disable_encoding" : True}
        )

        driver.set_page_load_timeout(30)

        return driver

    def request(self, flow):
        driver = self.get_chrome_driver()
        try:
            driver.get(flow.request.pretty_url)

            request = None
            url_to_find = flow.request.pretty_url.lower()
            for r in driver.requests:
                if(r.url.lower() == url_to_find):
                    if(r.response == None):
                        continue
                    elif(r.response.status_code == 200):
                        request = r
                        break
                    elif(r.response.status_code in [301,302,307,308]):
                        url_to_find = r.response.headers["Location"].lower()
                elif(r.url.lower() == driver.current_url.lower()):
                    request = r

            if(request == None):
                # print(f"Request not found for url: {flow.request.pretty_url}, {driver.current_url}")
                # for request in driver.requests:
                #     print(request.url, request.response.status_code if request.response != None else "")
                return

            headers = dict(request.response.headers)

            # body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))

            flow.response = http.Response.make(
                request.response.status_code,
                # body,
                request.response.body,
                headers
            )

            # for key, value in headers.items():
            #     if(key.lower() not in ["content-encoding", "transfer-encoding", "content-length"]):
            #         flow.response.headers[key] = value
        except Exception as e:
            logging.error(e)
        finally:
            if(driver != None):
                driver.close()
                driver.quit()
                driver = None

addons = [SeleniumClient()]
