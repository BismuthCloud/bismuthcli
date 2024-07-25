import os
import pytest
from typing import Optional
from unittest import mock
from urllib.parse import urlparse


TEST_AUTH = 'testauth123'
TEST_CONFIG = {
    "SOME_KEY": "SOME_VALUE",
}

class MockResponse:
    def __init__(self, text: Optional[str], status_code: int):
        self.text = text
        self.status_code = status_code

    def __repr__(self):
        return f"<{__class__.__name__} status_code={self.status_code} text={self.text}>"

    @property
    def ok(self):
        return 200 <= self.status_code < 300

def mock_get(url, **kwargs):
    if kwargs.get('headers', {}).get('Authorization', '') != "Bearer " + TEST_AUTH:
        return MockResponse(None, 401)
    p = urlparse(url)
    if not p.path.startswith("/secrets/v1/"):
        return MockResponse(None, 404)
    key = p.path[len("/secrets/v1/"):]
    if key in TEST_CONFIG:
        return MockResponse(TEST_CONFIG[key], 200)
    else:
        return MockResponse(None, 404)


@pytest.fixture(autouse=True)
def mock_svcprovider():
    os.environ['BISMUTH_AUTH'] = TEST_AUTH
    with mock.patch.multiple('requests', get=mock_get):
        yield


def test_get_existant_key():
    from .configuration import Configuration
    config = Configuration()
    assert config.get('SOME_KEY') == "SOME_VALUE"


def test_get_nonexistant_key():
    from .configuration import Configuration
    with pytest.raises(AttributeError):
        _ = Configuration().get('NONEXISTANT')
