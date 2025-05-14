"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
import logging

def request(flow):
    flow.request.path = "/ia5" + flow.request.path
