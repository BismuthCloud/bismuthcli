import os
import pytest
from flask import Request
from unittest.mock import MagicMock
from .api_code_block import APICodeBlock
from .function_code_block import FunctionCodeBlock


# Fixture to setup the APICodeBlock with mocked routes
@pytest.fixture
def api_block():
    os.environ["BISMUTH_AUTH"] = "TEST_AUTH"
    api_block = APICodeBlock()
    api_block.app.testing = True
    return api_block


def test_request_passed_through_auth_callback(api_block):
    def request_passed(request: Request):
        if type(request) != Request:
            return 500
        else:
            return 200

    api_block.add_route("/request_passed", {"GET": request_passed})

    with api_block.app.test_client() as client:
        response = client.get("/request_passed")
        assert response.status_code == 200


def test_add_route(api_block):
    mock_block = MagicMock(spec=FunctionCodeBlock)
    mock_block.exec.return_value = {"message": "mock response"}
    api_block.add_route("/mock", {"get": mock_block})

    with api_block.app.test_client() as client:
        response = client.get("/mock")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}
        mock_block.exec.assert_called_once()


def test_add_route_bare_func(api_block):
    def func(*args):
        return {"message": "mock response"}

    api_block.add_route("/mock", {"get": func})

    with api_block.app.test_client() as client:
        response = client.get("/mock")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}


def test_add_root_route(api_block):
    mock_block = MagicMock(spec=FunctionCodeBlock)
    mock_block.exec.return_value = {"message": "mock response"}
    api_block.add_route("/", {"get": mock_block})

    with api_block.app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}
        mock_block.exec.assert_called_once()
