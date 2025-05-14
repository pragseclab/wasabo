"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
import logging
import hashlib
import random
import string

def request(flow):
    if("msgID" not in flow.request.query):
        flow.request.query["msgID"] = ''.join(random.choice(string.ascii_letters) for x in range(10))
