import json
import os
import requests
from flask import request
from http import HTTPStatus
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from .data_storage_code_block import DataStorageCodeBlock


class PersistentDataStorageCodeBlock(DataStorageCodeBlock):
    """
    This class makes data storage operations persistent using Bismuth's blob storage service,
    allowing JSON-encodable objects to be persisted.
    """
    # A dictionary of HTTP headers used to authenticate to the storage backend.
    _auth: Dict[str, str]
    # The URL of the storage backend.
    _api_url: str

    def __init__(self, api_url="http://169.254.169.254:9000/blob/v1/"):
        """
        Initialize the datastore.
        """
        if 'BISMUTH_AUTH' not in os.environ:
            raise Exception("Missing BISMUTH_AUTH token in environment.")
        self._auth = {"Authorization": "Bearer " + os.environ['BISMUTH_AUTH']}
        self._api_url = api_url

    def _headers(self):
        hdrs = self._auth.copy()
        try:
            for tracehdr in ["traceparent", "tracestate"]:
                if tracehdr in request.headers:
                    hdrs[tracehdr] = request.headers[tracehdr]
        except RuntimeError:
            pass
        return hdrs

    def create(self, key, value) -> None:
        """Create a new item in the datastore."""
        resp = requests.post(urljoin(self._api_url, key), data=json.dumps(value), headers=self._headers())
        if resp.status_code == HTTPStatus.CONFLICT:
            raise ValueError("Key already exists.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def retrieve(self, key) -> Optional[Any]:
        """Retrieve an item from the datastore."""
        resp = requests.get(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        elif not resp.ok:
            raise Exception(f"Server error {resp}")
        return resp.json()

    def update(self, key, value) -> None:
        """Update an existing item in the datastore."""
        resp = requests.put(urljoin(self._api_url, key), data=json.dumps(value), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def delete(self, key) -> None:
        """Delete an item from the datastore."""
        resp = requests.delete(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def list_all(self) -> Dict[str, Any]:
        """List all items in the datastore."""
        resp = requests.get(self._api_url, headers=self._headers())
        if not resp.ok:
            raise Exception(f"Server error {resp}")
        return dict((k, json.loads(bytes(v))) for k, v in resp.json().items())
