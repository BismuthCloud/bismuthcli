from typing import Optional, Any, Callable
from flask import Flask, request
from flask_restx import Api, Resource
from .auth_code_block import AuthCodeBlock
from .base_code_block import BaseCodeBlock
from .configuration_code_block import ConfigurationCodeBlock
from .function_code_block import FunctionCodeBlock


class APICodeBlock(BaseCodeBlock):
    def __init__(
        self,
        title="API",
        version="1.0",
        description="A simple API",
        config: Optional[ConfigurationCodeBlock] = None,
        auth_code_block: Optional[AuthCodeBlock] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.app = Flask(__name__)
        @self.app.route("/healthz")
        def healthz():
            return "ok"

        if config is None:
            config = ConfigurationCodeBlock()

        self.config = config
        # Hack: set prefix so that this doesn't register over the root route
        self.api = Api(self.app, version=version, title=title, description=description, doc="/doc", prefix="/tmp")
        # And clear it
        self.api.prefix = ""
        self.auth_code_block = auth_code_block

    def _auth_handler(
        self,
        method: str,
        handlers: dict[str, FunctionCodeBlock | Callable[..., Any]],
        require_auth: list[str],
        **kwargs: Any
    ) -> Any:
        cb: Callable[..., Any] = handlers[method].exec if isinstance(handlers[method], FunctionCodeBlock) else handlers[method]

        if (
            method.upper() in map(lambda x: x.upper(), require_auth)
            and self.auth_code_block is not None
        ):
            return self.auth_code_block.token_required(cb)(**kwargs)
        else:
            return cb(**kwargs)

    def add_route(
        self,
        route: str,
        handlers: dict[str, FunctionCodeBlock | Callable[..., Any]],
        require_auth: list[str] = ["POST", "DELETE", "PUT"],
    ):
        handlers = {k.upper(): v for k, v in handlers.items()}
        auth_handler = self._auth_handler

        class DynamicResource(Resource):
            def get(self):
                kwargs = request.args.to_dict()
                if "GET" in handlers:
                    return auth_handler("GET", handlers, require_auth, **kwargs)
                else:
                    self.api.abort(404)

            def post(self):
                kwargs = request.json or {}
                if "POST" in handlers:
                    return auth_handler("POST", handlers, require_auth, **kwargs)
                else:
                    self.api.abort(404)

            def put(self):
                kwargs = request.json or {}
                if "PUT" in handlers:
                    return auth_handler("PUT", handlers, require_auth, **kwargs)
                else:
                    self.api.abort(404)

            def delete(self):
                kwargs = request.args.to_dict()

                if "DELETE" in handlers:
                    return auth_handler("DELETE", handlers, require_auth, **kwargs)
                else:
                    self.api.abort(404)

        self.api.add_resource(DynamicResource, route)

    def __call__(self, *args):
        return self.app(*args)

    def run(self, host="0.0.0.0", port=5000, debug=False):
        self.app.run(host=host, port=port, debug=debug)
