from bismuth import APICodeBlock, FunctionCodeBlock
from flask import Request

class HelloWorldAPI(APICodeBlock):
    def __init__(self):
        super().__init__()
        self.add_route("/hello", {"GET": FunctionCodeBlock(self.hello)})

    def hello(self, request: Request):
        return "hi"
