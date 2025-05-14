"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http

def response(flow):
    # print(flow.response.content.decode("utf-8"))
    print("Headers from tool: ", flow.request.headers)
    print()
    print("Headers from site: ", flow.response.headers)
