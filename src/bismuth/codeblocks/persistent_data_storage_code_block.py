import json
import os
import pathlib
import requests
import shutil
from flask import request
from http import HTTPStatus
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from .data_storage_code_block import DataStorageCodeBlock


class PersistentDataStorageCodeBlock(DataStorageCodeBlock):
    """
    This class makes data storage operations persistent using Bismuth's blob storage service,
    allowing JSON-encodable objects to be persisted.
    When run locally, it stores data via files in a temporary directory.
    """

    def __init__(self, api_url="http://169.254.169.254:9000/blob/v1/"):
        """
        Initialize the datastore.
        """
        if 'BISMUTH_AUTH' in os.environ:
            self._impl = HostedPersistentDataStorageCodeBlock(os.environ['BISMUTH_AUTH'], api_url)
        else:
            self._impl = LocalPersistentDataStorageCodeBlock()

    def create(self, key, value) -> None:
        """Create a new item in the datastore."""
        return self._impl.create(key, value)

    def retrieve(self, key) -> Optional[Any]:
        """Retrieve an item from the datastore."""
        return self._impl.retrieve(key)

    def update(self, key, value) -> None:
        """Update an existing item in the datastore."""
        return self._impl.update(key, value)

    def delete(self, key) -> None:
        """Delete an item from the datastore."""
        return self._impl.delete(key)

    def list_all(self) -> Dict[str, Any]:
        """List all items in the datastore."""
        return self._impl.list_all()


class HostedPersistentDataStorageCodeBlock(DataStorageCodeBlock):
    # A dictionary of HTTP headers used to authenticate to the storage backend.
    _auth: Dict[str, str]
    # The URL of the storage backend.
    _api_url: str

    def __init__(self, auth: str, api_url="http://169.254.169.254:9000/blob/v1/"):
        self._auth = {"Authorization": "Bearer " + auth}
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
        resp = requests.post(urljoin(self._api_url, key), data=json.dumps(value), headers=self._headers())
        if resp.status_code == HTTPStatus.CONFLICT:
            raise ValueError("Key already exists.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def retrieve(self, key) -> Optional[Any]:
        resp = requests.get(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        elif not resp.ok:
            raise Exception(f"Server error {resp}")
        return resp.json()

    def update(self, key, value) -> None:
        resp = requests.put(urljoin(self._api_url, key), data=json.dumps(value), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def delete(self, key) -> None:
        resp = requests.delete(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def list_all(self) -> Dict[str, Any]:
        resp = requests.get(self._api_url, headers=self._headers())
        if not resp.ok:
            raise Exception(f"Server error {resp}")
        return dict((k, json.loads(bytes(v))) for k, v in resp.json().items())


class LocalPersistentDataStorageCodeBlock(DataStorageCodeBlock):
    _dir = pathlib.Path("/tmp/bismuth_persistent_storage/")

    def create(self, key, value) -> None:
        path = self._dir / key
        if path.exists():
            raise ValueError("Key already exists.")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dir / key, 'w') as f:
            json.dump(value, f)

    def retrieve(self, key) -> Optional[Any]:
        path = self._dir / key
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return json.load(f)

    def update(self, key, value) -> None:
        path = self._dir / key
        if not path.exists():
            raise ValueError("Key does not exist.")
        with open(self._dir / key, 'w') as f:
            json.dump(value, f)

    def delete(self, key) -> None:
        path = self._dir / key
        if not path.exists():
            raise ValueError("Key does not exist.")
        path.unlink()

    def list_all(self) -> Dict[str, Any]:
        out = {}
        for fn in self._dir.glob('**/*'):
            with open(fn, 'r') as f:
                out[str(fn.relative_to(self._dir))] = json.load(f)
        return out

    def clear(self) -> None:
        if self._dir.exists():
            shutil.rmtree(self._dir)