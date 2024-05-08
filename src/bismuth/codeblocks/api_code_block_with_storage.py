from typing import Callable
from flask import Flask, request
from flask_restx import Api, Resource
from .api_code_block import APICodeBlock
from .data_storage_code_block import DataStorageCodeBlock
from .auth_code_block import AuthCodeBlock
from .function_code_block import FunctionCodeBlock


class APICodeBlockWithStorage(APICodeBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_stores = {}  # Dictionary to hold DataStorageBlock instances

    def _auth_handler_for_storage(
        self, method, func: FunctionCodeBlock | Callable, require_auth, **kwargs
    ):
        cb = func.exec if isinstance(func, FunctionCodeBlock) else func

        if (
            method.upper() in map(lambda x: x.upper(), require_auth)
            and self.auth_code_block is not None
        ):
            return self.auth_code_block.token_required(func.exec)(**kwargs)
        else:
            return func.exec(**kwargs)

    def add_route_with_storage(
        self,
        route,
        methods,
        data_storage_block: DataStorageCodeBlock,
        require_auth=["POST", "DELETE", "PUT"],
        auth_code_block: AuthCodeBlock = None,
    ):
        self.data_stores[route] = data_storage_block
        methods = methods if isinstance(methods, list) else [methods]
        methods = [method.upper() for method in methods]

        if auth_code_block is None:
            self.auth_code_block = AuthCodeBlock()
        else:
            self.auth_code_block = auth_code_block

        auth_handler_for_storage = self._auth_handler_for_storage

        class DynamicResource(Resource):
            def get(self):
                if "GET" in methods:
                    def run():
                        key = request.args.get("key")
                        return (
                            data_storage_block.retrieve(key)
                            if key
                            else data_storage_block.list_all()
                        )

                    func = FunctionCodeBlock(run)

                    return auth_handler_for_storage("GET", func, require_auth)
                else:
                    self.api.abort(405)

            def post(self):
                if "POST" in methods:
                    def run():
                        data = request.json
                        key, value = data.get("key"), data.get("value")
                        if key and value:
                            data_storage_block.create(key, value)
                            return {"message": "Item created"}, 201
                        else:
                            return {"message": "Key and value required"}, 400

                    func = FunctionCodeBlock(run)
                    return auth_handler_for_storage("POST", func, require_auth)
                else:
                    self.api.abort(405)

            def put(self):
                if "PUT" in methods:
                    def run():
                        data = request.json
                        key, value = data.get("key"), data.get("value")
                        if key and value:
                            data_storage_block.update(key, value)
                            return {"message": "Item updated"}
                        else:
                            return {"message": "Key and value required"}, 400

                    return auth_handler_for_storage("PUT", run, require_auth)
                else:
                    self.api.abort(405)

            def delete(self):
                self._auth_handler()
                if "DELETE" in methods:
                    def run():
                        key = request.args.get("key")
                        if key:
                            data_storage_block.delete(key)
                            return {"message": "Item deleted"}
                        else:
                            return {"message": "Key required"}, 400

                    func = FunctionCodeBlock(run)
                    return auth_handler_for_storage("DELETE", func, require_auth)

        self.api.add_resource(DynamicResource, route)
