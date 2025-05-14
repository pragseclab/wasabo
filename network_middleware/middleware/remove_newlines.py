"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
from pyblake2 import blake2b
from urllib.parse import urlparse
import logging

def calculate_checksum(data: bytes) -> bytes:
    """Calculate a checksum for raw data."""
    hasher = blake2b()
    hasher.update(data)
    return hasher.hexdigest()

def remove_newlines(data):
    try:
        new_data = data.decode("utf-8").replace("\n", "").encode()
    except Exception as e:
        logging.error(e)
        return data
    return new_data

def response(flow):
    path = urlparse(flow.request.pretty_url).path
    if(path == "/" or path == ""):
        return
    print(flow.request.pretty_url, calculate_checksum(flow.response.content))
    flow.response.content = remove_newlines(flow.response.content)
    print(flow.request.pretty_url, calculate_checksum(flow.response.content))

# def request(flow):
#     response = requests.get(flow.request.pretty_url)

#     flow.response = http.Response.make(
#             response.status_code,
#             response.content,
#     )

#     for key, value in response.headers.items():
#         flow.response.headers[key] = value
