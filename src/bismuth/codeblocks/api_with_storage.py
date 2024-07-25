from typing import Callable, Dict, List
from flask import request, Request
from flask_restx import Resource
from .api import API
from .data_storage import DataStorage


class APIWithStorage(API):
    """
    A class that extends APICodeBlock to include functionalities for data storage.
    It manages API routes and associates them with specific data storage operations.
    """
    # A dictionary that holds instances of DataStorageCodeBlock, used for managing data storage.
    data_stores: Dict[str, DataStorage]

    def __init__(self, *args, **kwargs):
        """
        Initializes the APICodeBlockWithStorage instance.
        Inherits initialization from APICodeBlock and initializes a dictionary to hold DataStorageBlock instances.
        """
        super().__init__(*args, **kwargs)
        self.data_stores = {}

    def add_route_with_storage(
        self,
        route: str,
        methods: List[str],
        data_storage_block: DataStorage,
        require_auth: List[str] = ["POST", "DELETE", "PUT"],
        auth_cb: Callable[[Request], bool] = lambda r: True,
    ):
        """
        Adds a route to the API with associated data storage functionality.
        """
        self.data_stores[route] = data_storage_block
        methods = methods if isinstance(methods, list) else [methods]
        methods = [method.upper() for method in methods]

        class DynamicResource(Resource):
            def get(self):
                if "GET" in methods:
                    if "GET" in require_auth and not auth_cb(request):
                        return self.api.abort(401)

                    key = request.args.get("key")
                    return (
                        data_storage_block.retrieve(key)
                        if key
                        else data_storage_block.list_all()
                    )
                else:
                    self.api.abort(405)

            def post(self):
                if "POST" in methods:
                    if "POST" in require_auth and not auth_cb(request):
                        return self.api.abort(401)

                    data = request.json
                    key, value = data.get("key"), data.get("value")
                    if key and value:
                        data_storage_block.create(key, value)
                        return {"message": "Item created"}, 201
                    else:
                        return {"message": "Key and value required"}, 400
                else:
                    self.api.abort(405)

            def put(self):
                if "PUT" in methods:
                    if "PUT" in require_auth and not auth_cb(request):
                        return self.api.abort(401)

                    data = request.json
                    key, value = data.get("key"), data.get("value")
                    if key and value:
                        data_storage_block.update(key, value)
                        return {"message": "Item updated"}
                    else:
                        return {"message": "Key and value required"}, 400
                else:
                    self.api.abort(405)

            def delete(self):
                self._auth_handler()
                if "DELETE" in methods:
                    if "DELETE" in require_auth and not auth_cb(request):
                        return self.api.abort(401)

                    key = request.args.get("key")
                    if key:
                        data_storage_block.delete(key)
                        return {"message": "Item deleted"}
                    else:
                        return {"message": "Key required"}, 400

        self.api.add_resource(DynamicResource, route)
