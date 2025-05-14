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

def remove_newlines(data):
    try:
        new_data = data.decode("utf-8").replace("\n", "").encode()
    except:
        return data
    return new_data


def get_chrome_driver() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('prefs', {'safebrowsing.enabled': False})
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=' + user_agent)

    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["Platform"] = "WINDOWS"
    caps["platformVersion"] = "10"

    driver = webdriver.Chrome(
        options=chrome_options,
        desired_capabilities=caps,
        seleniumwire_options={"disble_encoding" : True}
    )

    driver.set_page_load_timeout(10)

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



def request(flow):
    driver = get_chrome_driver()
    try:
        driver.get(flow.request.pretty_url)
    except Exception as e:
        logging.error(e)
        pass
    request = driver.requests[0]
    for r in driver.requests:
        if(r.url == driver.current_url):
            request = r


    headers = dict(request.response.headers)

    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    body = remove_newlines(body)
    # body = request.response.body
    # if(type(body) == str):
    #     body = body.encode()
    #     print(body)
    #     if("Content-Encoding" in headers):
    #         del headers["Content-Encoding"]
    # else:
    #     print("Bytes: " + flow.request.pretty_url)

    flow.response = http.Response.make(
        request.response.status_code,
        body,
    )

    # for key, value in headers.items():
    #     flow.response.headers[key] = value

    driver.close()
    driver.quit()
