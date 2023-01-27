from flask import Blueprint

admlog = Blueprint('admlogviewer', __name__)

from . import views
