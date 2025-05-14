"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
import requests
import hashlib

def response(flow):
    requests_response = requests.get(flow.request.pretty_url,
            headers = {"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15"})

    default_hash = hashlib.md5(flow.response.content).hexdigest()
    requests_hash = hashlib.md5(requests_response.content).hexdigest()

    print(f"{flow.request.pretty_url}, {flow.response.status_code}, {default_hash}, {requests_response.status_code}, {requests_hash}")
