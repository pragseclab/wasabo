"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
from urllib.parse import urlparse
from pyblake2 import blake2b
import logging
import re


def calculate_checksum(data: bytes) -> bytes:
    """Calculate a checksum for raw data."""
    hasher = blake2b()
    hasher.update(data)
    return hasher.hexdigest()

def response(flow):
    print(flow.request.pretty_url, calculate_checksum(flow.response.content))
