from bismuth import API
from flask import Request

class HelloWorldAPI(API):
    def __init__(self):
        super().__init__()
        self.add_route("/hello", {"GET": self.hello})

    def hello(self, request: Request):
        return "hi"

if __name__ == "__main__":
    HelloWorldAPI().run()