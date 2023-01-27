from flask import Blueprint

branch = Blueprint('branch', __name__)

from . import views, errors
