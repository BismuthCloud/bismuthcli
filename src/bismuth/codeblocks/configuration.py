import os
import requests
from flask import request
from http import HTTPStatus
from typing import Optional
from urllib.parse import urljoin

from .base_code_block import BaseCodeBlock


class Configuration(BaseCodeBlock):
    """
    The ConfigurationCodeBlock provides access to runtime configuration set outside the code.
    Instances of this class expose configuration to the application via the get method,
    which must be passed a string literal, NOT a variable.
    All instances of this class must be called `config`.
    """

    def __init__(self, api_url="http://169.254.169.254:9000/secrets/v1/"):
        """
        Initialize the configuration store.
        """
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
        """
        Get a config value. Raises an exception if the key does not exist in the managed configuration store.
        """
        if 'BISMUTH_AUTH' not in os.environ:
            raise Exception("Missing BISMUTH_AUTH token in environment.")
        resp = requests.get(urljoin(self.api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise AttributeError(f"Configuration key {key} not set")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")
        return resp.text
