from flask import Blueprint

dbviewer = Blueprint('dbviewer', __name__)

from . import views
