"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
import logging
import hashlib

def response(flow):
    print(hashlib.md5(flow.response.content).hexdigest())
