import json
import os
import pytest
from typing import Optional, Dict
from unittest import mock
from urllib.parse import urlparse

from .persistent_data_storage_code_block import PersistentDataStorageCodeBlock


TEST_AUTH = 'testauth123'


class MockResponse:
    def __init__(self, data: Optional[str | bytes], status_code: int):
        self.data = data
        self.status_code = status_code

    def __repr__(self):
        return f"<{__class__.__name__} status_code={self.status_code}>"

    def json(self):
        if self.data is None:
            return None
        return json.loads(self.data)

    @property
    def ok(self):
        return 200 <= self.status_code < 300

def mock_get(storage, url, **kwargs):
    if kwargs.get('headers', {}).get('Authorization', '') != 'Bearer ' + TEST_AUTH:
        return MockResponse(None, 401)
    p = urlparse(url)
    if p.path == "/blob/v1/":
        # svcprovider JSONifies the entire KV store here, and Rust JSON serializes byte arrays as [int].
        return MockResponse(json.dumps({k: list(v) for k,v in storage.items()}), 200)
    elif p.path.startswith("/blob/v1/"):
        key = p.path[len("/blob/v1/"):]
        if key in storage:
            return MockResponse(storage[key], 200)
        else:
            return MockResponse(None, 404)

def mock_post(storage, url, **kwargs):
    if 'Authorization' not in kwargs.get('headers', {}):
        return MockResponse(None, 401)
    p = urlparse(url)
    key = p.path[len("/blob/v1/"):]
    if key in storage:
        return MockResponse(None, 409)
    else:
        storage[key] = bytes(kwargs['data'], 'utf-8')
        return MockResponse(None, 200)

def mock_put(storage, url, **kwargs):
    if 'Authorization' not in kwargs.get('headers', {}):
        return MockResponse(None, 401)
    p = urlparse(url)
    key = p.path[len("/blob/v1/"):]
    if key in storage:
        storage[key] = bytes(kwargs['data'], 'utf-8')
        return MockResponse(None, 200)
    else:
        return MockResponse(None, 404)

def mock_delete(storage, url, **kwargs):
    if 'Authorization' not in kwargs.get('headers', {}):
        return MockResponse(None, 401)
    p = urlparse(url)
    key = p.path[len("/blob/v1/"):]
    if key in storage:
        del storage[key]
        return MockResponse(None, 200)
    else:
        return MockResponse(None, 404)


@pytest.fixture(autouse=True)
def mock_svcprovider():
    os.environ['BISMUTH_AUTH'] = TEST_AUTH
    storage: Dict[str, bytes] = {}
    with mock.patch.multiple('requests',
                             get=lambda url, **kwargs: mock_get(storage, url, **kwargs),
                             post=lambda url, **kwargs: mock_post(storage, url, **kwargs),
                             put=lambda url, **kwargs: mock_put(storage, url, **kwargs),
                             delete=lambda url, **kwargs: mock_delete(storage, url, **kwargs)):
        yield


def test_create_and_retrieve_item():
    storage = PersistentDataStorageCodeBlock()
    storage.create("test_key", "test_value")
    assert storage.retrieve("test_key") == "test_value"


def test_update_item():
    storage = PersistentDataStorageCodeBlock()
    storage.create("test_key", "test_value")
    storage.update("test_key", "new_test_value")
    assert storage.retrieve("test_key") == "new_test_value"


def test_delete_item():
    storage = PersistentDataStorageCodeBlock()
    storage.create("test_key", "test_value")
    storage.delete("test_key")
    assert storage.retrieve("test_key") is None


def test_create_existing_key():
    storage = PersistentDataStorageCodeBlock()
    storage.create("test_key", "test_value")
    with pytest.raises(ValueError):
        storage.create("test_key", "another_value")


def test_update_nonexistent_key():
    storage = PersistentDataStorageCodeBlock()
    with pytest.raises(ValueError):
        storage.update("nonexistent_key", "value")


def test_list_all_items():
    storage = PersistentDataStorageCodeBlock()
    storage.create("key1", "value1")
    storage.create("key2", "value2")
    all_items = storage.list_all()
    assert all_items == {"key1": "value1", "key2": "value2"}
