from flask import Blueprint

references = Blueprint('references', __name__)

from . import views
