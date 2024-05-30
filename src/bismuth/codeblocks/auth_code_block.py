from abc import ABC, abstractmethod
from typing import Optional
from functools import wraps
from flask import request, jsonify
from .base_code_block import BaseCodeBlock


class AuthService(ABC):
    @abstractmethod
    def validate_token(self, token) -> bool:
        """
        Validate the given token is authenticated
        """


class AuthCodeBlock(BaseCodeBlock):
    """
    Extends BaseCodeBlock. This class provides authentication functionalities for API endpoints.
    """
    # Holds the instance of the authentication service used for token validation.
    auth_service: AuthService

    def __init__(self, auth_service: Optional[AuthService] = None):
        """
        Initializes the AuthCodeBlock instance with a given authentication service.
        """
        if auth_service is None:
            self.auth_service = MockAuthService()
        else:
            self.auth_service = auth_service

    def token_required(self, f):
        """
        A decorator method to enforce token validation on API endpoints.
        It checks for a valid authentication token in the request header.
        """
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
