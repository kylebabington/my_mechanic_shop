# application/utils/util.py
# Token utilities (JWT encode/decode) + route protection decorator.

from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify, current_app
from jose import jwt
import jose


def encode_token(customer_id: int) -> str:
    """
    Create a JWT token that "belongs" to a specific customer.
    The 'sub' claim (subject) stores the customer_id as a STRING.
    """
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),

        "iat": datetime.now(timezone.utc),

        "sub": str(customer_id),
    }

    secret_key = current_app.config["SECRET_KEY"]
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def token_required(route_func):
    """
    Decorator that:
    - expects Authorization: Bearer <token>
    - validates token signature + expiration
    - extracts customer_id from token payload ('sub')
    - passes customer_id into wrapped route function
    """
    @wraps(route_func)
    def wrapper(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header missing or malformed."}), 401

        token = auth_header.split(" ")[1]

        try:
            secret_key = current_app.config["SECRET_KEY"]

            data = jwt.decode(token, secret_key, algorithms=["HS256"])

            customer_id = int(data["sub"])

        except jose.exceptions.ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401

        except jose.exceptions.JWTError:
            return jsonify({"message": "Invalid token."}), 401

        return route_func(customer_id, *args, **kwargs)

    return wrapper