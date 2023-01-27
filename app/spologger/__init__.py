from flask import Blueprint

spolog = Blueprint('spologviewer', __name__)

from . import views
