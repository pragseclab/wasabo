"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
from pyblake2 import blake2b
from urllib.parse import urlparse
import logging

def response(flow):
    del flow.response.headers["transfer-encoding"]

# def request(flow):
#     response = requests.get(flow.request.pretty_url)

#     flow.response = http.Response.make(
#             response.status_code,
#             response.content,
#     )

#     for key, value in response.headers.items():
#         flow.response.headers[key] = value
