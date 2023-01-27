# -*- coding: utf-8 -*-

import os
from flask_login import login_user, logout_user
from werkzeug.urls import url_quote, url_unquote


#from passlib.hash import pbkdf2_sha256 as hasher

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, IsPageClosed, page_redirect, errorlog, print_to, print_exception,
     default_unicode, default_encoding, LOG_PATH, LOG_NAME
     )

from . import auth
from ..import db, babel

from ..decorators import user_required
from ..utils import normpath, monthdelta, unquoted_url, decode_base64, getDate, getToday
from ..models import User, register_user, get_users, send_email, load_system_config
from ..settings import *

from .forms import LoginForm, ChangePasswordForm, ResetPasswordRequestForm, PasswordResetForm, RegistrationForm

IsResponseNoCached = 0

_EMERGENCY_EMAILS = ('mkaro.xx@gmail.com',)
_LOGIN_MESSAGE = 'Please log in to access this page.'
_MIN_REGISTERED_USER = 1
_MODULE = 'auth'

##  ===========================
##  User Authentication Package
##  ===========================


def is_valid_pwd(x):
    v = len(x) > 9 or (len(x) > 7 and
        len(re.sub(r'[\D]+', '', x)) > 0 and
        len(re.sub(r'[\d]+', '', x)) > 0 and
        len(re.sub(r'[\w]+', '', x)) > 0) \
        and True or False
    return v

def is_pwd_changed(user):
    return True

def send_message(user, token, **kw):
    subject = 'SSPDSA Reset Password Request'
    html = render_template('auth/reset_password_email.html', user=user, token=token, **kw)

    addr_to = [user.email]
    addr_cc = _EMERGENCY_EMAILS

    return send_email(subject, html, user, addr_to, addr_cc=addr_cc)

def send_password_reset_email(user, **kw):
    token = user.get_reset_password_token()
    done = send_message(user, token, **kw)
    return done and token or ''

def get_default_url(user=None):
    next = request.args.get('next')
    url = next not in ('', '/') and next or user is not None and user.base_url or None
    if url and IsResponseNoCached:
        return '%s%svsc=%s' % (url, '?' in url and '&' or '?', vsc()[1:])
    return url or 'default'

def menu(force=None):
    kw = make_platform()
    if kw.get('is_mobile') or force:
        kw.update({
            'navigation' : get_navigation(),
            'title'      : maketext('Application Main Menu'),
            'module'     : 'auth',
            'width'      : 1280,
            'message'    : maketext('Main menu').upper(),
            'vsc'        : vsc(),
        })
        return render_template('default.html', **kw)
    return redirect(url_for('main.default_route'))


## =========================== ##

@babel.localeselector
def get_locale():
    return get_request_item('locale') or DEFAULT_LANGUAGE


def _init():
    setup_locale()
    g.maketext = maketext
    g.app_product_name = maketext(connection_params.is_main and 'AppMainProductName' or 'AppProductName')

    load_system_config(g.current_user)

    today = getDate(getToday(), format=LOCAL_EASY_DATESTAMP)
    log = normpath(os.path.join(basedir, LOG_PATH, '%s_%s.log' % (today, LOG_NAME)))

    g.users_registered_required = False

    setup_logging(log)


@auth.before_app_request
def before_request():
    g.current_user = current_user
    g.engine = None

    if IsDeepDebug:
        print('--> before_request:is_authenticated:%s is_active:%s' % (current_user.is_authenticated, current_user.is_active))

    if not request.endpoint:
        return

    if IsTrace and IsDeepDebug:
        print_to(errorlog, '--> before_request endpoint:%s' % request.endpoint)

    if request.endpoint != 'static':
        _init()

    if request.endpoint[:5] != 'auth.' and request.endpoint != 'static' and not current_user.is_authenticated:
        pass

    if current_user.is_authenticated and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
        if not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        if not is_pwd_changed(current_user):
            current_user.unconfirmed()
            return redirect(url_for('auth.change_password'))
        if request.blueprint in APP_MODULES and request.endpoint.endswith('start'):
            current_user.ping()
        if IsPageClosed and (request.blueprint in page_redirect['items'] or '*' in page_redirect['items']) and \
            current_user.login not in page_redirect['logins'] and 'loader' not in request.url:
            if 'onservice' in page_redirect['base_url']:
                url = url_for('auth.onservice') + '?next=%s' % url_quote(request.full_path)
            else:
                url = '%s%s' % (page_redirect['base_url'], request.full_path)
            return redirect(url)


@auth.route('/index', methods=['GET'])
def started():
    users = get_users()

    if IsDebug:
        print_to(None, '--> before_request:is_authenticated:%s is_active:%s urls:%s endpoint: %s users:%s' % (
            current_user.is_authenticated, current_user.is_active, 
            (url_for('auth.started'), url_for('auth.login'), url_for('auth.register'), url_for('admin.start')),
            request.endpoint, len(users)
            ))

    if len(users) >= _MIN_REGISTERED_USER:
        g.users_registered_required = True
        return 1
    return 0


@auth.route('/login', methods=['GET', 'POST'])
def login():
    agent = request.user_agent

    if IsDebug:
        print_to(None, '--> current_user.is_active:%s agent: %s, users_registered_required:%s' % (current_user.is_active, agent, 
            g.users_registered_required and 1 or 0))

    title = 'Application Login'

    app_logger(_MODULE, title, is_info=True)

    if agent.browser is not None and not g.users_registered_required:
        if not started():
            clearFlash(_LOGIN_MESSAGE)
            return redirect(url_for('auth.register'))
        else:
            clearFlash(_LOGIN_MESSAGE, is_save_one=1)

    try:
        form = LoginForm()
        login = form.login.data
    except:
        login = None

    if login and form.validate_on_submit():
        user = User.query.filter_by(login=login).first()
    else:
        user = None

    def _get_root(link):
        x = accessed_link.split('/')
        return len(x) > 1 and x[1] or link

    accessed_link = get_default_url(user)
    root = _get_root(accessed_link)

    if agent.browser is None:
        authorization = request.authorization

        login, password = '', ''

        try:
            if not authorization:
                login, password = decode_base64(request.headers.get('X-User-Authorization')).decode().split(':')
            else:
                login = authorization.username
                password = authorization.password

            if IsTrace:
                print_to(None, '!!! auth.login [%s:%s], headers:%s, remote_addr:%s' % (
                    login, 
                    password, 
                    repr(request.headers), 
                    request.remote_addr
                    ))

            user = User.query.filter_by(login=login).first()

            if user is not None and user.is_user:
                is_valid_password = user.verify_password(password)
                is_confirmed = user.confirmed
                is_enabled = user.enabled

                if is_confirmed and is_enabled and is_valid_password:
                    login_user(user)

                return redirect(accessed_link)

        except Exception as ex:
            print_to(None, '!!! auth.login.error %s [%s], headers:%s, remote_addr:%s' % (
                repr(authorization), 
                str(ex), 
                repr(request.headers), 
                request.remote_addr
                ))

            if IsPrintExceptions:
                print_exception()

        abort(401)

    elif user is not None:
        is_valid_password = user.verify_password(form.password.data)
        is_admin = user.is_administrator()
        is_confirmed = user.confirmed
        is_enabled = user.enabled

        if IsDeepDebug:
            print('--> user:%s valid:%s enabled:%s is_admin:%s' % (user and user.login, 
                is_valid_password, is_enabled, is_admin))

        IsEnabled = False

        if not user.is_user or not is_enabled:
            flash('Access to the application is denied!')
        elif not is_valid_password:
            flash('Password is incorrect!')
        elif not is_confirmed:
            flash('You should change you password!')
            accessed_link = url_for('auth.change_password')
            IsEnabled = True
        elif 'admin' in accessed_link and not is_admin:
            flash('You cannot access this page!')
        else:
            IsEnabled = True

        if IsDeepDebug:
            print('--> link:%s enabled:%s' % (accessed_link, IsEnabled))

        if IsTrace:
            print_to(errorlog, '\n==> login:%s %s enabled:%s' % (user.login, request.remote_addr, is_valid_password), request=request)

        if IsEnabled:
            try:
                login_user(user, remember=form.remember_me.data)
            except Exception as ex:
                print_to(errorlog, '!!! auth.login error: %s %s' % (login, str(ex)))
                if IsPrintExceptions:
                    print_exception()

            if accessed_link in ('default', '/'):
                return menu()

            return redirect(accessed_link)

    elif login:
        if IsTrace:
            print_to(errorlog, '\n==> login:%s is invalid!!! %s' % (login, request.remote_addr,))

        flash('Invalid username or password.')

    debug, kw = init_response(title, mode=_MODULE)

    if kw.get('error'):
        kw.update({
            'module'        : _MODULE,
            'request'       : repr(request),
            'user_agent'    : {
                'browser'   : agent.browser, 
                'platform'  : agent.platform, 
                'string'    : agent.string,
                },
            'authorization' : request.authorization,
            'endpoint'      : request.endpoint,
            'host'          : request.host,
            'remote_addr'   : request.remote_addr,
            'method'        : request.method,
            'args'          : request.args,
            'user'          : repr(user),
        })

        if IsDebug:
            """
            fo = open(errorlog, mode='a')
            json.dump(kw, fo, sort_keys=True, indent=4)
            fo.close()
            """

            print_to(errorlog, json.dumps(kw, sort_keys=True, indent=4))

        return jsonify(kw['error'])

    kw.update({
        'module'        : _MODULE,
        'title'         : title,
        'page_title'    : maketext('Application Auth'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    return render_template('auth/login.html', form=form, **kw)


@auth.route('/default', methods=['GET', 'POST'])
def default():
    return menu(1)

@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    return make_response('auth change email form')


@auth.route('/profile', methods=['GET'])
def profile():
    return make_response('auth user profile form')


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if IsDeepDebug:
        print('--> change password:is_active:%s' % current_user.is_active)

    title = maketext('Application Change Password')

    app_logger(_MODULE, title, is_info=True)

    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            if form.old_password.data == form.password.data:
                flash('Duplicate password.')
            elif not is_valid_pwd(form.password.data):
                flash('Invalid password syntax.')
            else:
                current_user.change_password(form.password.data)
                flash('Your password has been updated.')
                return default()
        else:
            flash('Invalid password.')
    elif not form.old_password.data:
        pass
    else:
        flash('ChangePasswordForm data is invalid.')

    if IsDeepDebug:
        print('--> password invalid: [%s-%s-%s]' % (form.old_password.data, form.password.data, form.password2.data))

    kw = make_platform(mode=_MODULE)

    kw.update({
        'title'         : title,
        'page_title'    : maketext('Application Reset Password'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : _MODULE,
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    link = 'auth/change_password.html'

    return render_template(link, form=form, **kw)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return default()

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for('auth.login'))

    title = maketext('Application Reset Password')

    app_logger(_MODULE, title, is_info=True)

    form = PasswordResetForm()

    if form.validate_on_submit():
        password = form.password.data
        if not is_valid_pwd(password):
            flash('Invalid password syntax.')
        else:
            user.change_password(password)
            user.ping()
            flash('Your password has been reset.')
            return redirect(url_for('auth.login'))
    
    elif form.errors:
        for x in form.errors.get('password'):
            flash(x)

    kw = make_platform(mode=_MODULE)

    kw.update({
        'title'         : title,
        'page_title'    : maketext('Forced Reset Password Form'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : _MODULE,
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    link = 'auth/reset_password.html'

    return render_template(link, form=form, **kw)


@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if IsDeepDebug:
        print('--> reset password request:is_active:%s' % current_user.is_active)

    if current_user.is_authenticated:
        return default()

    title = maketext('Application Reset Password Request')

    app_logger(_MODULE, title, is_info=True)

    form = ResetPasswordRequestForm()

    link = 'auth/reset_password_request.html'

    kw = make_platform(mode=_MODULE)

    kw.update({
        'title'         : title,
        'page_title'    : maketext('Reset Password Request Form'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : _MODULE,
    })

    if form.validate_on_submit():
        token = None
        user = User.query.filter_by(email=form.email.data).first()
        kw['greeting'] = user and ', %s' % user.full_name() or ''
        if user:
            token = send_password_reset_email(user, **kw)
        if token:
            flash('Check your email for the instructions to reset your password')
        else:
            flash('Error sending Reset Password Request email')
        kw['error'] = not token and 1 or 0
        kw['token'] = token and url_for('auth.reset_password', token=token, _external=True) or ''
        link = 'auth/reset_password_done.html'

    kw['vsc'] = vsc()

    return render_template(link, form=form, **kw)


@auth.route('/logout')
@login_required
def logout():
    app_logger('auth', maketext('User Logout'), is_info=True)
    logout_user()
    clearFlash(_LOGIN_MESSAGE)
    flash(maketext('You have been logged out.'))
    return redirect(url_for('auth.login'))


@auth.route('/branch')
@login_required
def branch():
    logout_user()
    return redirect(url_for('branch.start')+'?sidebar=0&short=1')


@auth.route('/forbidden')
def forbidden():
    abort(403)


@auth.route('/onservice')
def onservice():
    if not IsPageClosed:
        next = request.args.get('next')
        return redirect(next or '/')
        
    kw = make_platform(mode=_MODULE)

    kw.update({
        'title'        : maketext('Application Login'),
        'page_title'   : maketext('Application Auth'),
        'header_class' : 'middle-header',
        'show_flash'   : True,
        'semaphore'    : {'state' : ''},
        'sidebar'      : {'state' : 0, 'title' : ''},
        'module'       : 'auth',
        'message'      : page_redirect.get('message') or maketext('Software upgrade'),
    })

    kw['vsc'] = vsc()

    return render_template('auth/onservice.html', **kw)


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for('auth.login'))

    kw = make_platform(mode=_MODULE)

    kw.update({
        'title'        : maketext('Application Unconfirmed'),
        'page_title'   : maketext('Application Reset Password'),
        'header_class' : 'middle-header',
        'show_flash'   : True,
        'semaphore'    : {'state' : ''},
        'sidebar'      : {'state' : 0, 'title' : ''},
        'module'       : _MODULE,
    })

    kw['vsc'] = vsc()

    return render_template('auth/unconfirmed.html', **kw)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('auth.default'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('auth.default'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if IsDebug:
        print_to(None, '--> auth.register')

    authorization = request.authorization

    title = 'User Register'

    try:
        form = RegistrationForm()
    except:
        form = None

    try:
        if form is None:
            pass
        elif not form.login.data:
            pass
        elif form is not None and form.validate_on_submit():
            user = None
            """
            user = User(email=form.email.data.lower(),
                        login=form.login.data,
                        password=form.password.data,
                        name=(form.first_name.data, form.family_name.data, form.last_name.data),
                        role=int(form.role.data),
                        confirmed=True,
                        enabled=true,
                    )
            db.session.add(user)
            db.session.commit()
            """
            form = RegistrationForm(request.form)
            IsOk, user, errors = register_user(form, None)

            if IsOk and user is not None:
                token = user.generate_confirmation_token()
                html ="""token:%s""" % token
                if send_email('Confirm Your Account', html, user, user.email) and not IsNoEmail:
                    flash('A confirmation email has been sent to you by email.')
                else:
                    flash('A new user has been successfully added.')
                return redirect(url_for('auth.login'))
            else:
                for error in errors:
                    flash(error)
        else:
            flash('Invalid register form. Please, repeat')

    except Exception as ex:
            print_to(None, '!!! auth.register.error %s [%s], headers:%s, remote_addr:%s' % (
                repr(authorization), 
                str(ex), 
                repr(request.headers), 
                request.remote_addr
                ))

            if IsPrintExceptions:
                print_exception()

            g.app_logger('auth.register', 'User register error. See traceback.log for details', is_error=True)

            flash(msg)

    debug, kw = init_response(title, mode=_MODULE)

    if kw.get('error'):
        kw.update({
            'request'       : repr(request),
            'user_agent'    : {
                'browser'   : agent.browser, 
                'platform'  : agent.platform, 
                'string'    : agent.string,
                },
            'authorization' : request.authorization,
            'endpoint'      : request.endpoint,
            'host'          : request.host,
            'remote_addr'   : request.remote_addr,
            'method'        : request.method,
            'args'          : request.args,
            'user'          : repr(user),
        })

        if IsDebug:
            print_to(errorlog, json.dumps(kw, sort_keys=True, indent=4))

        return jsonify(kw['error'])

    kw.update({
        'page_title'    : maketext('User Register Form'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'show_password' : not IsEdge() and 1 or 0,
        'module'        : _MODULE,
        'model'         : 0,
    })

    return render_template('auth/register.html', form=form, **kw)

