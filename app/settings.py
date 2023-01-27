# -*- coding: utf-8 -*-

import re
import sys
import random
import decimal
import json
from datetime import datetime
import pytz
import logging

# https://pypi.org/project/user-agents/
from user_agents import parse as user_agent_parse

from flask import (
     Response, abort, render_template, url_for, redirect, request, make_response, jsonify, flash, stream_with_context, 
     g, session, current_app
     )
from flask_login import login_required, current_user
from flask_babel import gettext
from flask import json

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsLogTrace, IsShowLoader, IsForceRefresh, IsPrintExceptions, IsDisableOutput, IsFlushOutput,
     IsAppCenter, IsAppBranch, IsPublic, IsFuture, IsNoEmail,
     basedir, errorlog, print_to, print_exception, default_system_locale, 
     CONNECTION, ConnectionParams, connection_params,
     LOCAL_EASY_DATESTAMP, UTC_FULL_TIMESTAMP, LOCAL_EASY_TIMESTAMP, LOCAL_EASY_DATESTAMP, PUBLIC_URL, 
     getCurrentDate, isIterable,
     TIMEZONE, TIMEZONE_COMMON_NAME
)

from .patches import is_limited, is_forbidden
from .utils import getToday, getDate
from .messages import MESSAGES


def setup_locale():
    import os
    import locale
    import platform

    if locale.getlocale()[0] is None:
        locale.setlocale(locale.LC_ALL, default_system_locale)
    info = {'loc': locale.getlocale(), 'lod_def': locale.getdefaultlocale()}

    if IsDeepDebug and IsLogTrace:
        print_to(None, '>>> locale: %s os:%s platform:%s' % (info,  os.name, platform.system()))


def maketext(key, lang=None, force=None):
    text = gettext(key)
    if text == key or force:
        if key in MESSAGES:
            text = MESSAGES[key][lang or DEFAULT_LANGUAGE]
    return text or key


#
#   DON'T IMPORT utils HERE !!!
#

product_version = ('0.7', 'Beta, 2023-01-15')

#########################################################################################

#   -------------
#   Default types
#   -------------

DEFAULT_LANGUAGE = 'ru'
DEFAULT_LOG_MODE = 1
DEFAULT_PER_PAGE = 10
DEFAULT_OPER_PER_PAGE = 50
DEFAULT_MANAGER_PER_PAGE = 20
DEFAULT_ADMIN_PER_PAGE = 10
DEFAULT_PAGE = 1
DEFAULT_UNDEFINED = '---'
DEFAULT_DATE_FORMAT = ('%d/%m/%Y', '%Y-%m-%d',)
DEFAULT_DATETIME_FORMAT = '<nobr>%Y-%m-%d</nobr><br><nobr>%H:%M:%S</nobr>'
DEFAULT_DATETIME_INLINE_FORMAT = '<nobr>%Y-%m-%d</nobr> <nobr>%H:%M:%S</nobr>' #'<nobr>%Y-%m-%d&nbsp;%H:%M:%S</nobr>'
DEFAULT_DATETIME_INLINE_SHORT_FORMAT = '<nobr>%Y-%m-%d</nobr><br><nobr>%H:%M</nobr>'
DEFAULT_DATETIME_PERSOLOG_FORMAT = ('%Y%m%d', '%Y-%m-%d %H:%M:%S',)
DEFAULT_DATETIME_SDCLOG_FORMAT = ('%d.%m.%Y', '%d.%m.%Y %H:%M:%S,%f',)
DEFAULT_DATETIME_EXCHANGELOG_FORMAT = ('%d.%m.%Y', '%Y-%m-%d %H:%M:%S.%f',)
DEFAULT_DATETIME_READY_FORMAT = '%b %d %Y %I:%M%p'
DEFAULT_DATETIME_TODAY_FORMAT = '%d.%m.%Y'
DEFAULT_HTML_SPLITTER = '_'
DEFAULT_USER_AVATAR = ('<img class="avatar" src="%s" title="%s" alt="%s">', '/static/img/person-default.jpg', '', 'jpg', (40, None))

USE_FULL_MENU = True

MAX_TITLE_WORD_LEN = 50
MAX_XML_TREE_NODES = 100
MAX_LOGS_LEN = 99999
MAX_LINK_LENGTH = 100
MAX_CONFIRMATION_LEN = 8000
MAX_UPLOADED_IMAGE = 10**8
EMPTY_VALUE = '...'
EMPTY_REFERENCE_VALUE = ' - не задано - '

# action types
VALID_ACTION_TYPES = ('101', '301',)

default_locale = 'rus'

SEMAPHORE = {
    'count'    : 7,
    'timeout'  : 5000,
    'action'   : '901',
    'speed'    : '100:1000',
    'seen_at'  : (5,10,),
    'inc'      : (1,1,1,1,1,1,1,),
    'duration' : (9999, 5000, 0, 0, 0, 3000, -1,),
}

PROCESS_INFO = {
}

DATE_KEYWORDS = ('today', 'yesterday', 'tomorrow',)
EXTRA_ = '__'


APP_MODULES = (
    'auth',
    'admin',
    'main',
    'equipment',
    'center',
    'branch',
    'configurator',
    'references',
    'maintenance',
    'admlogviewer',
    'spologviewer',
)

APP_MENUS = [
    'default',
    'configurator',
    'references',
    'dbviewer',
    'logviewer',
    'main',
]

CALENDAR_HOLIDAYS = ()
CALENDAR_WORKDAYS = ()

CEO_LOGIN = ''

## ================================================== ##


class DataEncoder(json.JSONEncoder):
    def default(self, ob):
        if isinstance(ob, decimal.Decimal):
            return str(ob)
        return json.JSONEncoder.default(self, ob)


def app_logger(mode, message, force=None, is_error=False, is_warning=False, is_info=False, data=None, **kw):
    #
    #   g.app_logger
    #
    if IsDisableOutput:
        return
    line = ': mode[{mode:<12}] : {ip} : {host} : login=[{login:<10}] : {message} {data}'.format(
        mode= mode,
        ip= request.remote_addr,
        host= kw.get('host') or request.form.get('host') or request.host_url,
        login= g.current_user.is_authenticated and g.current_user.login or 'AnonymousUser',
        message= message,
        data= data and '\n%s' % data or '',
    )
    if IsDeepDebug:
        print_to(None, line)
    if IsLogTrace:
        if is_error:
            g.app_logging.error(line)
        elif is_warning:
            g.app_logging.warning(line)
        elif IsTrace and (force or is_info):
            g.app_logging.info(line)
    if IsFlushOutput:
        sys.stdout.flush()


def setup_logging(log):
    try:
        if g.app_logger is not None:
            return
    except:
        pass

    P_TIMEZONE = pytz.timezone(TIMEZONE)

    logging.basicConfig(
        filename=log,
        format='%(asctime)s : %(name)s-%(levelname)s >>> %(message)s', 
        level=logging.DEBUG, 
        datefmt=UTC_FULL_TIMESTAMP,
    )

    g.app_logging = logging.getLogger(__name__)
    g.app_logger = app_logger


def clearFlash(msg, is_save_one=None):
    key = '_flashes'
    if key not in session:
        return
    is_exist = 0
    for i, (m, x) in enumerate(session[key]):
        if msg == x:
            is_exist = 1
        if not x:
            pass
    if is_exist:
        session['_flashes'].clear()
    if is_save_one:
        flash(msg)


_agent = None
_user_agent = None

def IsAndroid():
    return _agent.platform == 'android'
def IsiOS():
    return _agent.platform == 'ios' or 'iOS' in _user_agent.os.family
def IsiPad():
    return _agent.platform == 'ipad' or 'iPad' in _user_agent.os.family
def IsLinux():
    return _agent.platform == 'linux'
def IsAstra():
    return _agent.platform == 'linux' and _agent.browser == 'firefox'

def IsChrome():
    return _agent.browser == 'chrome'
def IsFirefox():
    return _agent.browser == 'firefox'
def IsSafari():
    return _agent.browser == 'safari' or 'Safari' in _user_agent.browser.family
def IsOpera():
    return _agent.browser == 'opera' or 'Opera' in _user_agent.browser.family

def IsIE(version=None):
    ie = _agent.browser.lower() in ('explorer', 'msie',)
    if not ie:
        return False
    elif version:
        return float(_agent.version) == version
    return float(_agent.version) < 10
def IsSeaMonkey():
    return _agent.browser.lower() == 'seamonkey'
def IsEdge():
    return 'Edge' in _agent.string
def IsMSIE():
    return _agent.browser.lower() in ('explorer', 'ie', 'msie', 'seamonkey',) or IsEdge()

def IsMobile():
    return IsAndroid() or IsiOS() or IsiPad() or _user_agent.is_mobile or _user_agent.is_tablet
def IsNotBootStrap():
    return IsIE(10) or IsAndroid()
def IsWebKit():
    return IsChrome() or IsFirefox() or IsOpera() or IsSafari()

def BrowserVersion():
    return _agent.version

def BrowserInfo(force=None):
    mobile = 'IsMobile:[%s]' % (IsMobile() and '1' or '0')
    info = 'Browser:[%s] %s Agent:[%s]' % (_agent.browser, mobile, _agent.string)
    browser = IsMSIE() and 'IE' or IsOpera() and 'Opera' or IsChrome() and 'Chrome' or IsFirefox() and 'FireFox' or IsSafari() and 'Safari' or None
    if force:
        return info
    return browser and '%s:%s' % (browser, mobile) or info

## -------------------------------------------------- ##

def get_request_item(name, check_int=None, args=None, is_iterable=None):
    if args:
        x = args.get(name)
    elif request.method.upper() == 'POST':
        if is_iterable:
            return request.form.getlist(name)
        else:
            x = request.form.get(name)
    else:
        x = None
    if not x and (not check_int or (check_int and x in (None, ''))):
        x = request.args.get(name)
    if check_int:
        if x in (None, ''):
            return None
        elif x.isdigit():
            return int(x)
        elif ':' in x:
            return x
        elif x in 'yY':
            return 1
        elif x in 'nN':
            return 0
        else:
            return None
    if x:
        if x == DEFAULT_UNDEFINED or x.upper() == 'NONE':
            x = None
        elif x.startswith('{') and x.endswith('}'):
            return eval(re.sub('null', '""', x))
    return x or ''

def get_request_items():
    return request.method.upper() == 'POST' and request.form or request.args

def has_request_item(name):
    return name in request.form or name in request.args

def get_request_search():
    return get_request_item('reset_search') != '1' and get_request_item('search') or ''

def get_page_params(view=None):
    is_admin = g.current_user.is_administrator(private=True)
    is_manager = g.current_user.is_manager(private=True)
    is_operator = g.current_user.is_operator(private=True)

    page = 0
    per_page = int(get_request_item('per_page') or get_request_item('per-page') or 0)

    default_per_page = view and g.current_user.get_pagesize(view) or DEFAULT_PER_PAGE
    
    try:
        if not per_page:
            per_page = default_per_page
        else:
            g.current_user.set_pagesize(view, per_page)
        page = int(get_request_item('page') or DEFAULT_PAGE)
    except:
        if IsPrintExceptions:
            print_exception()
        per_page = default_per_page
        page = DEFAULT_PAGE
    finally:
        if per_page <= 0 or per_page > 1000:
            per_page = default_per_page
        if page <= 0:
            page = DEFAULT_PAGE

    next = get_request_item('next') and True or False
    prev = get_request_item('prev') and True or False

    if next:
        page += 1
    if prev and page > 1:
        page -= 1

    return page, per_page

def default_user_avatar(user=None):
    return DEFAULT_USER_AVATAR[0] % (DEFAULT_USER_AVATAR[1], user and user.get_user_post() or DEFAULT_USER_AVATAR[2], user and user.login or '')

def make_platform(mode=None, debug=None):
    global _agent, _user_agent

    agent = request.user_agent
    browser = agent.browser

    if browser is None:
        return { 'error' : 'Access is not allowed!' }

    os = agent.platform
    root = '%s/' % request.script_root

    _agent = agent
    _user_agent = user_agent_parse(agent.string)

    is_astra = ('%s' % (_user_agent)) == 'PC / Linux / Firefox 90.0' and 1 or 0

    if IsTrace and g.system_config.IsLogAgent:
        print_to(errorlog, 'user_agent:[%s]' % _user_agent)
        print_to(errorlog, '\n==> os:[%s], astra[%s], agent:%s[%s], browser:%s' % (os, is_astra, repr(agent), _user_agent, browser), request=request)

    is_owner = False
    is_admin = False
    is_manager = True
    is_operator = False
    is_superuser = False

    avatar = None
    sidebar_collapse = False

    try:
        is_superuser = g.current_user.is_superuser(private=True)
        is_owner = g.current_user.is_owner()
        is_admin = g.current_user.is_administrator(private=False)
        is_manager = g.current_user.is_manager(private=True)
        is_operator = g.current_user.is_operator(private=True)
        avatar = g.current_user.get_avatar()

        if has_request_item('sidebar'):
            sidebar_collapse = get_request_item('sidebar', check_int=True) == 0 and True or False
            if sidebar_collapse != g.current_user.sidebar_collapse:
                g.current_user.sidebar_collapse = sidebar_collapse
        else:
            # By default Sidebar is expanded (state:0)
            sidebar_collapse = g.current_user.sidebar_collapse or False
    except:
        pass

    sidebar_state = not sidebar_collapse and 1 or 0

    referer = ''
    links = {}

    is_mobile = IsMobile()
    is_default = 1 or os in ('ipad', 'android',) and browser in ('safari', 'chrome',) and 1 or 0 
    is_frame = not is_mobile and 1 or 0

    version = agent.version
    css = IsMSIE() and 'ie' or is_mobile and 'mobile' or 'web'

    platform = '[os:%s, browser:%s (%s), css:%s, %s %s%s%s]' % (
        os, 
        browser, 
        version, 
        css, 
        default_locale, 
        is_default and ' default' or ' flex',
        is_frame and ' frame' or '', 
        debug and ' debug' or '',
    )

    kw = {
        'os'             : os, 
        'platform'       : platform,
        'root'           : root, 
        'back'           : '',
        'agent'          : agent.string,
        'version'        : version, 
        'browser'        : browser, 
        'browser_info'   : BrowserInfo(0),
        'is_linux'       : IsLinux() and 1 or 0,
        'is_astra'       : is_astra and 1 or 0,
        'is_demo'        : 0, 
        'is_frame'       : is_frame, 
        'is_mobile'      : is_mobile and 1 or 0,
        'is_superuser'   : is_superuser and 1 or 0,
        'is_admin'       : is_admin and 1 or 0,
        'is_operator'    : (is_operator or is_manager or is_admin) and not is_owner and 1 or 0,
        'is_show_loader' : IsShowLoader,
        'is_explorer'    : IsMSIE() and 1 or 0,
        'css'            : css, 
        'referer'        : referer, 
        'bootstrap'      : '',
        'model'          : 0,
    }

    if mode:
        kw[mode] = True

    kw['bootstrap'] = '-new' if mode in APP_MODULES else ''

    kw.update({
        'links'          : links, 
        'style'          : {'default' : is_default, 'header' : datetime.today().day%2==1 and 'dark' or 'light', 'show_scroller' : 0},
        'screen'         : request.form.get('screen') or '',
        'scale'          : request.form.get('scale') or '',
        'usertype'       : is_manager and 'manager' or is_operator and 'operator' or 'default',
        'sidebar'        : {'state' : sidebar_state, 'title' : gettext('Click to close top menu')},
        'avatar'         : avatar,
        'with_avatar'    : 1,
        'with_post'      : 1,
        'logo'           : '', 
        'image_loader'   : '%s%s' % (root, 'static/img/loader.gif'), 
        'is_main'        : connection_params.is_main
    })

    kw['is_active_scroller'] = 0 if IsMSIE() or IsFirefox() or is_mobile else (g.system_config.IsActiveScroller and 1 or 0)

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)

    if IsTrace and IsDeepDebug:
        print_to(errorlog, '--> make_platform:%s' % mode)

    return kw

def make_keywords():
    return (
    # --------------
    # Error Messages
    # --------------
    "'Execution error':'%s'" % gettext('Execution error'),
    # -------
    # Buttons
    # -------
    "'Add':'%s'" % gettext('Add'),
    "'Back':'%s'" % gettext('Back'),
    "'Calculate':'%s'" % gettext('Calculate'),
    "'Cancel':'%s'" % maketext('Cancel', force=1),
    "'Confirm':'%s'" % maketext('Confirm', force=1),
    "'Close':'%s'" % gettext('Close'),
    "'Execute':'%s'" % gettext('Execute'),
    "'Finished':'%s'" % gettext('Done'),
    "'Frozen link':'%s'" % gettext('Frozen link'),
    "'Link':'%s'" % gettext('Link'),
    "'OK':'%s'" % gettext('OK'),
    "'Open':'%s'" % gettext('Open'),
    "'Reject':'%s'" % maketext('Reject'),
    "'Rejected':'%s'" % gettext('Rejected'),
    "'Remove':'%s'" % gettext('Remove'),
    "'Run':'%s'" % gettext('Run'),
    "'Save':'%s'" % gettext('Save'),
    "'Search':'%s'" % gettext('Search'),
    "'Select':'%s'" % gettext('Select'),
    "'Update':'%s'" % gettext('Update'),
    # ----
    # Help
    # ----
    "'Attention':'%s'" % gettext('Attention'),
    "'All':'%s'" % gettext('All'),
    "'Commands':'%s'" % gettext('Commands'),
    "'Help':'%s'" % gettext('Help'),
    "'Help information':'%s'" % gettext('Help information'),
    "'Helper keypress guide':'%s'" % gettext('Helper keypress guide'),
    "'System information':'%s'" % gettext('System information'),
    "'Total':'%s'" % gettext('Total'),
    # --------------------
    # Flags & Simple Items
    # --------------------
    "'error':'%s'" % gettext('error'),
    "'yes':'%s'" % gettext('Yes'),
    "'no':'%s'" % gettext('No'),
    "'none':'%s'" % gettext('None'),
    "'true':'%s'" % 'true',
    "'false':'%s'" % 'false',
    # ------------------------
    # Miscellaneous Dictionary
    # ------------------------
    "'batch':'%s'" % gettext('batch'),
    "'Choose a File':'%s...'" % gettext('Choose a File'),
    "'Confirm notification form':'%s'" % gettext('Confirm notification form'),
    "'file':'%s'" % gettext('file'),
    "'Image view':'%s'" % gettext('Image view'),
    "'No data':'%s'" % gettext('No data'),
    "'No data or access denied':'%s'" % gettext('No data'),
    "'No documents':'%s'" % gettext('No documents'),
    "'Notification form':'%s'" % gettext('Notification form'),
    "'order confirmation':'%s'" % gettext('Are you really going to'),
    "'select referenced item':'%s:'" % gettext('Choice the requested item from the given list'),
    "'shortcut version':'%s'" % '1.0',
    "'status confirmation':'%s'" % gettext('Are you really going to change the status'),
    "'status confirmation request':'%s:'" % gettext('Choice the requested status from the given list'),
    "'please confirm':'%s.'" % gettext('Please, confirm'),
    "'Print processing info':'%s'" % gettext('Print processing info'),
    "'Processing info':'%s'" % gettext('Processing info'),
    "'Recovery is impossible!':'%s'" % gettext('Recovery is impossible!'),
    "'Status confirmation form':'%s'" % gettext('Status confirmation form'),
    "'top-close':'%s'" % gettext('Click to close top menu'),
    "'top-open':'%s'" % gettext('Click to open top menu'),
    # -------------
    # Notifications
    # -------------
    "'Admin Find':'%s'" % gettext('Find (name, login, email)'),
    "'Data corresponds to the current status':'%s'" % gettext('Data corresponds to the current status.'),
    "'Data will be filtered accordingly':'%s'" % gettext('Data will be filtered accordingly.'),
    "'Command:Do you really want to save changes':'%s'" % maketext('Command:Do you really want to save changes?'),
    "'Command:Config item removing':'%s'" % gettext('Command: Do you really want to remove the config item?'),
    "'Command:Config scenario removing':'%s'" % gettext('Command: Do you really want to remove the config scenario?'),
    "'Command:Item was changed. Continue?':'%s'" % gettext('Command: Item was changed. Continue?'),
    "'Command:Photo item removing. Continue?':'%s'" % gettext('Command: Photo item removing. Continue?'),
    "'Command:Send request to the warehouse':'%s'" % gettext('Command: Send request to the warehouse?'),
    "'Item will be removed from database!':'%s'" % gettext("Be carefull! Item will be removed from database."),
    "'Its not realized yet!':'%s'" % gettext("Sorry! Its not realized yet."),
    "'Message:Action was done successfully':'%s'" % gettext('Message: Action was done successfully.'),
    "'Message:Request sent successfully':'%s'" % gettext('Message: Request was sent successfully.'),
    "'Active Period':'%s'" % maketext('Active Period [begin, finish]:'),
    "'Technical equipment':'%s'" % maketext('Technical equipment:'),
    "'Value should be less then:':'%s'" % maketext('Value should be less then:'),
    "'Value should be more then:':'%s'" % maketext('Value should be more then:'),
    )


def init_response(title, mode):
    host = request.form.get('host') or request.host_url

    _title = '%s. %s' % (maketext('AppName'), maketext(title))

    app_logger(mode, 'Старт модуля "%s"' % _title, is_info=True, host=host)

    if 'debug' in request.args:
        debug = request.args['debug'] == '1' and True or False
    else:
        debug = None

    connection_params._init_state()
    if IsTrace:
        properties = sorted([p for p in dir(ConnectionParams) if isinstance(getattr(ConnectionParams, p), property)])
        params = connection_params.items
        print_to(None, '\n>>> CONNECTION PARAMS [updated: %s]' % getDate(getToday(), format=UTC_FULL_TIMESTAMP))
        for item in properties:
            if item in ('items'):
                continue
            value = getattr(connection_params, item)
            print_to(None, '... %s:[%s]' % (item, value))
        print_to(None, '%s\n' % ('-'*(40)))

    kw = make_platform(mode, debug=debug)
    keywords = make_keywords()
    forms = ('index', 'admin', 'main')

    now = datetime.today().strftime(DEFAULT_DATE_FORMAT[1])

    kw.update({
        'title'        : _title,
        'host'         : host,
        'locale'       : default_locale, 
        'language'     : 'ru',
        'keywords'     : keywords, 
        'forms'        : forms,
        'now'          : now,
        'action_id'    : get_request_item('action_id') or '0',
        'batch_id'     : get_request_item('batch_id') or '0',
        'event_id'     : get_request_item('event_id') or '0',
        'file_id'      : get_request_item('file_id') or '0',
        'oper_id'      : get_request_item('oper_id') or '0',
        'order_id'     : get_request_item('order_id') or '0',
        'pers_id'      : get_request_item('pers_id') or '0',
        'preload_id'   : get_request_item('preload_id') or '0',
        'review_id'    : get_request_item('review_id') or '0',
    })

    kw['selected_data_menu_id'] = get_request_item('selected_data_menu_id')
    kw['window_scroll'] = get_request_item('window_scroll')
    kw['avatar_width'] = '80'

    return debug, kw

def vsc(force=False):
    return (IsIE() or IsForceRefresh or force) and ('?%s' % str(int(random.random()*10**12))) or ''

def is_app_public():
    return IsPublic and request.host_url == PUBLIC_URL

def is_app_center():
    return IsAppCenter and not is_app_public() and 1 or 0

def is_app_branch():
    return IsAppBranch

def get_navigation():
    is_admin = g.current_user.is_administrator()
    is_superuser = g.current_user.is_superuser()
    is_manager = g.current_user.is_manager()
    is_operator = g.current_user.is_operator()
    is_any = g.current_user.is_any()
    is_nobody = g.current_user.is_nobody()

    items = []

    app_menu = g.current_user.app_menu
    base_url = g.current_user.base_url

    def _item(key):
        return key, '/%s' % key

    def _get_item_url(key):
        x = key in base_url and base_url or key
        return '%s%s' % (request.script_root, x.startswith('/') and x or '/' + x)

    if g.current_user.is_authenticated:
        if app_menu in ('center', 'default'):
            if is_superuser:
                """
                items.append({'link'  : '%s/admin/index' % request.script_root, 
                              'id'    : 'mainmenu-admin',
                              'title' : maketext('Application admin page'), 
                              'class' : ('/admin' in request.url or request.endpoint == 'admin.start') and 'selected' or ''})

                items.append({'link'  : '%s/auth/register' % request.script_root, 
                              'id'    : 'mainmenu-register',
                              'title' : maketext('User Register'), 
                              'class' : ('/register' in request.url or request.endpoint == 'auth.register') and 'selected' or ''})
                """
                pass

        if is_app_center() or is_app_branch():
            """
            items.append({'link'  : '%s/index?sidebar=0' % request.script_root, 
                          'id'    : 'mainmenu-main',
                          'title' : maketext('Application Main Menu'), 
                          'class' : ('/main' in request.url or request.endpoint == 'main.start') and 'selected' or ''})
            """
            if connection_params.is_main:
                items.append({'link'  : '%s/index/equipment' % request.script_root, 
                              'id'    : 'mainmenu-equipment',
                              'title' : maketext('Application Equipment'), 
                              'class' : ('equipment' in request.url or request.endpoint == 'main.start') and 'selected' or ''})

            items.append({'link'  : '%s/center/index' % request.script_root, 
                          'id'    : 'mainmenu-center-exchange',
                          'title' : maketext('Application Center Data Exchage'), 
                          'class' : ('center' in request.url and request.endpoint == 'center.start') and 'selected' or ''})

            items.append({'link'  : '%s/branch/index' % request.script_root, 
                          'id'    : 'mainmenu-branch-exchange',
                          'title' : maketext('Application Branch Data Exchage'), 
                          'class' : ('branch' in request.url and request.endpoint == 'branch.start') and 'selected' or ''})
            """
            items.append({'link'  : '%s/refers' % request.script_root, 
                          'id'    : 'references',
                          'title' : maketext('Application References'), 
                          'class' : ('refers' in request.url and request.endpoint == 'references.start') and 'selected' or ''})
            items.append({'link'  : '%s/services' % request.script_root, 
                          'id'    : 'maintenance',
                          'title' : maketext('Application Database Maintenance'), 
                          'class' : ('services' in request.url and request.endpoint == 'maintenance.start') and 'selected' or ''})
            """
        #items.append({'link' : '%s/auth/logout' % request.script_root, 'title': 'Выход', 'class':''})
    else:
        items.append({'link' : '%s/auth/login' % request.script_root, 'title': 'Вход', 'class':''})

    return items
