import os
import requests
from flask import request
from http import HTTPStatus
from typing import Optional
from urllib.parse import urljoin

from .base_code_block import BaseCodeBlock


class ConfigurationCodeBlock(BaseCodeBlock):
    """
    The ConfigurationCodeBlock provides access to configuration parameters set during creation.
    Any configured key is available through the get() method, returning the string value or raising an exception if no
    such configuration key exists.
    """

    def __init__(self, api_url="http://169.254.169.254:9000/secrets/v1/"):
        if 'BISMUTH_AUTH' not in os.environ:
            print("Missing BISMUTH_AUTH token in environment. Configuration will not be available.")
            return
        self.auth = {"Authorization": "Bearer " + os.environ['BISMUTH_AUTH']}
        self.api_url = api_url

    def _headers(self):
        hdrs = self.auth.copy()
        try:
            for tracehdr in ["traceparent", "tracestate"]:
                if tracehdr in request.headers:
                    hdrs[tracehdr] = request.headers[tracehdr]
        except RuntimeError:
            pass
        return hdrs

    def get(self, key) -> Optional[str]:
        if 'BISMUTH_AUTH' not in os.environ:
            raise Exception("Missing BISMUTH_AUTH token in environment.")
        resp = requests.get(urljoin(self.api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise AttributeError(f"Configuration key {key} not set")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")
        return resp.text
