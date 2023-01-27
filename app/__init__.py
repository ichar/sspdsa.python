# -*- coding: utf-8 -*-

from flask import Flask, render_template
#from flask_bootstrap import Bootstrap
from flask_mail import Mail
#from flask_moment import Moment
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_log_request_id import RequestID, current_request_id
#from flask.ext.pagedown import PageDown
from config import app_release, default_unicode, IsAppCenter, IsAppBranch, config

#bootstrap = Bootstrap()
babel = Babel()
mail = Mail()
#moment = Moment()
db = SQLAlchemy()
#pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'basic' # 'strong'
login_manager.login_view = 'auth.login'

from .patches import *


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.register_error_handler(403, forbidden)

    #bootstrap.init_app(app)
    babel.init_app(app)
    mail.init_app(app)
    #moment.init_app(app)
    db.init_app(app)

    login_manager.init_app(app)

    #pagedown.init_app(app)

    #if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #    from flask.ext.sslify import SSLify
    #    sslify = SSLify(app)

    RequestID(app)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth') 

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    if IsAppCenter or IsAppBranch:
        from .dbviewer import dbviewer as viewer_blueprint
        app.register_blueprint(viewer_blueprint, url_prefix='/db')

        from .configurator import configurator as configurator_blueprint
        app.register_blueprint(configurator_blueprint, url_prefix='/config')

        from .references import references as references_blueprint
        app.register_blueprint(references_blueprint, url_prefix='/refers')

        from .admlogger import admlog as admlogger_blueprint
        app.register_blueprint(admlogger_blueprint, url_prefix='/admlogs')

        from .spologger import spolog as spologger_blueprint
        app.register_blueprint(spologger_blueprint, url_prefix='/spologs')

        from .maintenance import maintenance as maintenance_blueprint
        app.register_blueprint(maintenance_blueprint, url_prefix='/services')

        from .center import center as center_blueprint
        app.register_blueprint(center_blueprint, url_prefix='/center')

        from .branch import branch as branch_blueprint
        app.register_blueprint(branch_blueprint, url_prefix='/branch')

        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

    from .semaphore import semaphore as semaphore_blueprint
    app.register_blueprint(semaphore_blueprint, url_prefix='/semaphore')

    from .dbviewer import dbviewer as dbviewer_blueprint
    app.register_blueprint(dbviewer_blueprint, url_prefix='/dbviewer')

    return app
