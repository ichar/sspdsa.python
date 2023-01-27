from flask import Blueprint

center = Blueprint('center', __name__)

from . import views, errors
