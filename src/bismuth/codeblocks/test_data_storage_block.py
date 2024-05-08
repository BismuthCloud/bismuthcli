# Writing pytest tests for the DataStorageBlock class

import pytest

from .data_storage_code_block import DataStorageCodeBlock


def test_create_and_retrieve_item():
    storage = DataStorageCodeBlock()
    storage.create("test_key", "test_value")
    assert storage.retrieve("test_key") == "test_value"


def test_update_item():
    storage = DataStorageCodeBlock()
    storage.create("test_key", "test_value")
    storage.update("test_key", "new_test_value")
    assert storage.retrieve("test_key") == "new_test_value"


def test_delete_item():
    storage = DataStorageCodeBlock()
    storage.create("test_key", "test_value")
    storage.delete("test_key")
    assert storage.retrieve("test_key") is None


def test_create_existing_key():
    storage = DataStorageCodeBlock()
    storage.create("test_key", "test_value")
    with pytest.raises(ValueError):
        storage.create("test_key", "another_value")


def test_update_nonexistent_key():
    storage = DataStorageCodeBlock()
    with pytest.raises(ValueError):
        storage.update("nonexistent_key", "value")


def test_list_all_items():
    storage = DataStorageCodeBlock()
    storage.create("key1", "value1")
    storage.create("key2", "value2")
    all_items = storage.list_all()
    assert all_items == {"key1": "value1", "key2": "value2"}
