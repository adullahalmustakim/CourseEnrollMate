from functools import wraps
from flask import session, redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "username" not in session:
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


def role_required(role):
    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            if session.get("role") != role:
                return "403 Forbidden: Unauthorized access"

            return f(*args, **kwargs)

        return decorated_function

    return decorator