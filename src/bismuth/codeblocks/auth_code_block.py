from functools import wraps
from flask import request, jsonify
from .base_code_block import BaseCodeBlock


class AuthCodeBlock(BaseCodeBlock):
    def __init__(self, auth_service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if auth_service is None:
            self.auth_service = MockAuthService()
        else:
            self.auth_service = auth_service

    def token_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None

            if "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

            if not token:
                return jsonify({"message": "Token is missing!"}), 401

            if not self.auth_service.validate_token(token):
                return jsonify({"message": "Token is invalid!"}), 401

            return f(*args, **kwargs)

        return decorated


# Example of a mocked authentication service
class MockAuthService:
    @staticmethod
    def validate_token(token):
        # Replace this with real validation logic
        return token == "valid_token"
