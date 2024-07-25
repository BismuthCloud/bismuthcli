# 2024-07-25: Ensures that we still have exports for the old *CodeBlock names.
# These are deprecated and should not be used in new projects.
from bismuth import APICodeBlock
from flask import Request

class HelloWorldAPI(APICodeBlock):
    def __init__(self):
        super().__init__()
        self.add_route("/hello", {"GET": self.hello})

    def hello(self, request: Request):
        return "hi"

if __name__ == "__main__":
    HelloWorldAPI().run()
