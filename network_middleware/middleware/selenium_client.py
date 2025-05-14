"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.chrome.options import Options
import os
import logging


class SeleniumClient:
    def __init__(self):
        self.trees = {}
        self.driver = self.get_chrome_driver()

    def get_chrome_driver(self) -> None:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """

        # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('prefs', {'safebrowsing.enabled': False})
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=' + user_agent)

        caps = webdriver.DesiredCapabilities.CHROME.copy()
        caps["Platform"] = "WINDOWS"
        caps["platformVersion"] = "10"
        caps["pageLoadStrategy"] = "eager"

        driver = webdriver.Chrome(
            options=chrome_options,
            desired_capabilities=caps,
            seleniumwire_options={"disable_encoding" : True}
        )

        driver.set_page_load_timeout(20)

        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})

        # Disable remote control flag
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source" : """
                Object.defineProperty(navigator, 'platform', {
                    value: 'Win32', configurable:true
                })
            """
        })

        # Set the platform to Windows
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source" : """
                Object.defineProperty(navigator, 'webdriver', {
                    value: undefined, configurable:true
                })
            """
        })

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'WINDOWS'})")

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
