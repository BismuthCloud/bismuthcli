import json
import pytest
from typing import Optional, Dict
from unittest import mock
from urllib.parse import urlparse

from .blob_storage import _HostedBlobStorage, _LocalBlobStorage


TEST_AUTH = 'testauth123'


class MockResponse:
    def __init__(self, content: Optional[str | bytes], status_code: int):
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.content = content
        self.status_code = status_code

    def __repr__(self):
        return f"<{__class__.__name__} status_code={self.status_code}>"

    def json(self):
        if self.content is None:
            return None
        return json.loads(self.content.decode('utf-8'))

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
        storage[key] = kwargs['data']
        return MockResponse(None, 200)

def mock_put(storage, url, **kwargs):
    if 'Authorization' not in kwargs.get('headers', {}):
        return MockResponse(None, 401)
    p = urlparse(url)
    key = p.path[len("/blob/v1/"):]
    if key in storage:
        storage[key] = kwargs['data']
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
    storage: Dict[str, bytes] = {}
    with mock.patch.multiple('requests',
                             get=lambda url, **kwargs: mock_get(storage, url, **kwargs),
                             post=lambda url, **kwargs: mock_post(storage, url, **kwargs),
                             put=lambda url, **kwargs: mock_put(storage, url, **kwargs),
                             delete=lambda url, **kwargs: mock_delete(storage, url, **kwargs)):
        yield


@pytest.fixture(params=[_HostedBlobStorage(TEST_AUTH), _LocalBlobStorage()])
def storage(request):
    if isinstance(request.param, _LocalBlobStorage):
        request.param.clear()
    return request.param


def test_create_and_retrieve_item(storage):
    storage.create("test_key", b"test_value")
    assert storage.retrieve("test_key") == b"test_value"


def test_update_item(storage):
    storage.create("test_key", b"test_value")
    storage.update("test_key", b"new_test_value")
    assert storage.retrieve("test_key") == b"new_test_value"


def test_delete_item(storage):
    storage.create("test_key", b"test_value")
    storage.delete("test_key")
    assert storage.retrieve("test_key") is None


def test_create_existing_key(storage):
    storage.create("test_key", b"test_value")
    with pytest.raises(ValueError):
        storage.create("test_key", b"another_value")


def test_update_nonexistent_key(storage):
    with pytest.raises(ValueError):
        storage.update("nonexistent_key", b"value")


def test_list_all_items(storage):
    storage.create("key1", json.dumps("value1").encode('utf-8'))
    storage.create("key2", json.dumps("value2").encode('utf-8'))
    assert storage.list_keys() == {"key1", "key2"}
