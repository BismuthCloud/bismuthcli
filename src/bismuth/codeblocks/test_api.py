import os
import pytest
from flask import Request
from .api import API
from .function import Function


# Fixture to setup the APICodeBlock with mocked routes
@pytest.fixture
def api_block():
    os.environ["BISMUTH_AUTH"] = "TEST_AUTH"
    api_block = API()
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
    def func(request, **kwargs):
        return {"message": "mock response"}

    api_block.add_route("/mock", {"get": Function(func)})

    with api_block.app.test_client() as client:
        response = client.get("/mock")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}


def test_add_route_bare_func(api_block):
    def func(request, **kwargs):
        return {"message": "mock response"}

    api_block.add_route("/mock", {"get": func})

    with api_block.app.test_client() as client:
        response = client.get("/mock")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}


def test_add_root_route(api_block):
    def func(request, **kwargs):
        return {"message": "mock response"}

    api_block.add_route("/", {"get": Function(func)})

    with api_block.app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json == {"message": "mock response"}


def test_json_kwargs(api_block):
    def func(request, **kwargs):
        return {"json": kwargs}

    api_block.add_route("/", {"post": Function(func)})

    with api_block.app.test_client() as client:
        response = client.post("/", json={"key": "value"})
        assert response.status_code == 200
        assert response.json == {"json": {"key": "value"}}


def test_non_json_request(api_block):
    def func(request, **kwargs):
        return {"data": request.get_data(as_text=True)}

    api_block.add_route("/", {"post": Function(func)})

    with api_block.app.test_client() as client:
        response = client.post("/", data={"form": "value"})
        assert response.status_code == 200
        assert response.json == {"data": "form=value"}
