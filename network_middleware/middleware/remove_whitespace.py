"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from mitmproxy import http
from urllib.parse import urlparse
from pyblake2 import blake2b
import logging
import re

class RemoveWhitespace:
    def __init__(self):
        pass

    def calculate_checksum(self, data: bytes) -> bytes:
        """Calculate a checksum for raw data."""
        hasher = blake2b()
        hasher.update(data)
        return hasher.hexdigest()

    def remove_comments(self, string):
        try:
            pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
            # first group captures quoted strings (double or single)
            # second group captures comments (//single-line or /* multi-line */)
            regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
            def _replacer(match):
                # if the 2nd group (capturing comments) is not None,
                # it means we have captured a non-quoted (real) comment string.
                if match.group(2) is not None:
                    return "" # so we will return empty to remove the comment
                else: # otherwise, we will return the 1st group
                    return match.group(1) # captured quoted-string
            return regex.sub(_replacer, string.decode()).encode()
        except:
            return string

    def remove_whitespace(self, data):
         try:
             new_data = "".join(data.decode("utf-8").split()).encode()
         except Exception as e:
             logging.error(e)
             return data
         return new_data

    def response(self, flow):
        path = urlparse(flow.request.pretty_url).path
        if(path == "/" or path == ""):
            return
        flow.response.content = self.remove_whitespace(self.remove_comments(flow.response.content))
        print(flow.request.pretty_url, self.calculate_checksum(flow.response.content))

addons = [RemoveWhitespace()]
