from bismuth import API
from functools import wraps
from flask import Request
from typing import Callable, Any

class AuthenticatedAPI(API):
    def __init__(self):
        super().__init__()
        self.add_route("/hello", {"GET": self.hello})

    @staticmethod
    def check_auth(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(self, request: Request, **kwargs):
            if request.headers.get("Authorization") == "Basic dXNlcjpwYXNz":  # user:pass
                return func(self, request, **kwargs)
            else:
                return "Unauthorized", 401
        return wrapper

    @check_auth
    def hello(self, request: Request):
        return "hi authenticated user!"

if __name__ == "__main__":
    AuthenticatedAPI().run()
