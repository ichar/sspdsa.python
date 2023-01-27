
from functools import wraps
from flask import abort, url_for, redirect, request, make_response, jsonify, flash
from flask_login import login_required, current_user

from .models import roles

##  =============================
##  Application Global Decorators
##  =============================

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(role):
                #abort(403)
                return redirect(url_for('auth.forbidden'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required(roles.ROOT)(f)


def user_required(f):
    return current_user.is_user

"""
def users_registered_required(f):
    return redirect(url_for('auth.start'))
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(role):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
"""

