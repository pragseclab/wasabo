"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
import requests

def request(flow):
    # headers={"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
    #         "Host" : "cal.replayforkids.org"}
    headers = {}

    for key, value in dict(flow.request.headers).items():
        if(key.lower() not in ["accept-encoding", "accept"]):
            headers[key] = value


    response = requests.get(flow.request.pretty_url, headers=headers, verify=False, allow_redirects=False)
    # response = requests.get(flow.request.pretty_url, headers=flow.request.headers, verify=False, allow_redirects=False)
    # response= requests.get(flow.request.pretty_url, headers=flow.request.headers)

    print(response.content.decode("utf-8"))
    print()
    print("Request headers from tool: ", dict(flow.request.headers))
    print("Request headers from middleware: ", response.request.headers)
    print()
    print("Response headers from site: ", response.headers)
    headers = dict(response.headers)

    flow.response = http.Response.make(
            response.status_code,
            response.content,
    )

    for key, value in response.headers.items():
        if(key.lower() not in ["content-encoding", "transfer-encoding", "content-length"]):
            flow.response.headers[key] = value

    print("Response headers from middleware: ", dict(flow.response.headers))
