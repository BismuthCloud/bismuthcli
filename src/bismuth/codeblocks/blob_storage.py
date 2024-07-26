import json
import os
import pathlib
import requests
import shutil
from flask import request
from http import HTTPStatus
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from .base_code_block import BaseCodeBlock


class BlobStorage(BaseCodeBlock):
    """
    This class exposes Bismuth's blob storage service, allowing data to be persisted.
    Bytes are stored plain, while other types are stored as JSON.
    When run locally, it stores data via files in a temporary directory.
    """

    def __init__(self, api_url="http://169.254.169.254:9000/blob/v1/"):
        """
        Initialize the datastore.
        """
        if 'BISMUTH_AUTH' in os.environ:
            self._impl = _HostedBlobStorage(os.environ['BISMUTH_AUTH'], api_url)
        else:
            self._impl = _LocalBlobStorage()

    def _encode(self, value) -> bytes:
        return value if isinstance(value, bytes) else json.dumps(value).encode('utf-8')

    def _decode(self, value) -> Optional[Any]:
        if value is None:
            return None
        try:
            return json.loads(value)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return value

    def create(self, key: str, value: Any) -> None:
        """Create a new item in the datastore."""
        return self._impl.create(key, self._encode(value))

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve an item from the datastore."""
        return self._decode(self._impl.retrieve(key))

    def update(self, key: str, value: Any) -> None:
        """Update an existing item in the datastore."""
        return self._impl.update(key, self._encode(value))

    def delete(self, key: str) -> None:
        """Delete an item from the datastore."""
        return self._impl.delete(key)

    def list_keys(self) -> set[str]:
        """List all keys in the datastore."""
        return self._impl.list_keys()


class _HostedBlobStorage(BaseCodeBlock):
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

    def create(self, key: str, value: bytes) -> None:
        resp = requests.post(urljoin(self._api_url, key), data=value, headers=self._headers())
        if resp.status_code == HTTPStatus.CONFLICT:
            raise ValueError("Key already exists.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def retrieve(self, key: str) -> Optional[bytes]:
        resp = requests.get(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        elif not resp.ok:
            raise Exception(f"Server error {resp}")
        return resp.content

    def update(self, key: str, value: bytes) -> None:
        resp = requests.put(urljoin(self._api_url, key), data=value, headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def delete(self, key: str) -> None:
        resp = requests.delete(urljoin(self._api_url, key), headers=self._headers())
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError("Key does not exist.")
        elif not resp.ok:
            raise Exception(f"Server error {resp}")

    def list_keys(self) -> set[str]:
        resp = requests.get(self._api_url, headers=self._headers())
        if not resp.ok:
            raise Exception(f"Server error {resp}")
        return set(resp.json().keys())


class _LocalBlobStorage(BaseCodeBlock):
    _dir = pathlib.Path("/tmp/bismuth_blob_storage/")

    def create(self, key: str, value: bytes) -> None:
        path = self._dir / key
        if path.exists():
            raise ValueError("Key already exists.")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dir / key, 'wb') as f:
            f.write(value)

    def retrieve(self, key: str) -> Optional[bytes]:
        path = self._dir / key
        if not path.exists():
            return None
        with open(path, 'rb') as f:
            return f.read()

    def update(self, key: str, value: bytes) -> None:
        path = self._dir / key
        if not path.exists():
            raise ValueError("Key does not exist.")
        with open(self._dir / key, 'wb') as f:
            f.write(value)

    def delete(self, key: str) -> None:
        path = self._dir / key
        if not path.exists():
            raise ValueError("Key does not exist.")
        path.unlink()

    def list_keys(self) -> set[str]:
        out = set()
        for fn in self._dir.glob('**/*'):
            out.add(str(fn.relative_to(self._dir)))
        return out

    def clear(self) -> None:
        if self._dir.exists():
            shutil.rmtree(self._dir)
