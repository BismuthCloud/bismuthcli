from typing import Optional, Any, Callable, Concatenate
from flask import Flask, Request, request
from flask_restx import Api, Resource
from .base_code_block import BaseCodeBlock
from .configuration import Configuration


class API(BaseCodeBlock):
    """
    Extends BaseCodeBlock, this class includes methods and attributes for API code blocks.
    """

    # The Flask application instance.
    app: Flask
    api: Api
    # The ConfigurationCodeBlock instance for this API.
    config: Configuration

    def __init__(
        self,
        title="API",
        version="1.0",
        description="A simple API",
        config: Optional[Configuration] = None,
        *args,
        **kwargs
    ):
        """
        Initializes the APICodeBlock class with optional title, version, description, and configuration code block.
        `add_route` should be called in overrides of this to register routes for the API.
        """
        super().__init__(*args, **kwargs)
        self.app = Flask(__name__)

        @self.app.route("/healthz")
        def healthz():
            return "ok"

        if config is None:
            config = Configuration()

        self.config = config
        # Hack: set prefix so that this doesn't register over the root route
        self.api = Api(
            self.app,
            version=version,
            title=title,
            description=description,
            doc="/doc",
            prefix="/tmp",
        )
        # And clear it
        self.api.prefix = ""

    def add_route(
        self,
        route: str,
        handlers: dict[str, Callable[Concatenate[Request, ...], Any]],
    ):
        """
        Adds a route to the API.
        Handlers receive the request from flask plus query parameters as kwargs.
        """
        handlers = {k.upper(): v for k, v in handlers.items()}

        class DynamicResource(Resource):
            def get(self):
                kwargs = request.args.to_dict()
                if "GET" in handlers:
                    return handlers["GET"](request, **kwargs)
                else:
                    self.api.abort(404)

            def post(self):
                kwargs = request.get_json(silent=True) or {}
                if "POST" in handlers:
                    return handlers["POST"](request, **kwargs)
                else:
                    self.api.abort(404)

            def put(self):
                kwargs = request.get_json(silent=True) or {}
                if "PUT" in handlers:
                    return handlers["PUT"](request, **kwargs)
                else:
                    self.api.abort(404)

            def delete(self):
                kwargs = request.args.to_dict()
                if "DELETE" in handlers:
                    return handlers["DELETE"](request, **kwargs)
                else:
                    self.api.abort(404)

        self.api.add_resource(DynamicResource, route)

    def __call__(self, *args):
        return self.app(*args)

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """
        Starts the API on the given port and host.
        """

        self.app.run(host=host, port=port, debug=debug)
