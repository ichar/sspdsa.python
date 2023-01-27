# -*- coding: utf-8 -*-

from config import (
     CONNECTION, CONFIG_PATH,
     LocalDebug
     )

from . import center

from ..settings import *
from ..models import get_users_dict
from ..pages import ViewRender
from ..sockets import Commander
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, Capitalize,
     checkPaginationRange,
     daydelta
     )

from .. import db

from .page_center import PageCenter


##  =====================
##  Center Viewer Package
##  =====================


default_page = 'center'
default_action = '800'
default_log_action = '801'
default_template = 'center'
default_title = 'Application Viewer'


IsLocalDebug = LocalDebug[default_page]


def before(f):
    def wrapper(**kw):
        name = kw.get('engine') or 'default'
        g.engine = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.requested_object = {}
    return

## ==================================================== ##

default_date_format = DEFAULT_DATE_FORMAT[1]

def _today():
    return getDate(getToday(), default_date_format)

def _check_extra_tabs(row):
    tabs = {}
    return tabs

def _valid_extra_action(action, row=None):
    return action

def _get_page_args():
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    try:
        args = { \
            'division'     : ['DIVISION', int(get_request_item('division') or 0)],
            'line'         : ['LINE', int(get_request_item('line') or 0)],
            'selected_date': ['TIMESTAMP', get_request_item('selected_date') or None],
            'date_from'    : ['TIMESTAMP', get_request_item('date_from') or None],
            'date_to'      : ['TIMESTAMP', get_request_item('date_to') or None],
            'user'         : ['LOGIN', get_request_item('user') or ''],
            'today'        : ['TIMESTAMP', get_request_item('today', check_int=1) or 0],
            'id'           : ['LID', int(get_request_item('_id') or '0')],
        }
    except:
        args = { \
            'division'     : ['DIVISION', 0],
            'line'         : ['LINE', 0],
            'selected_date': ['TIMESTAMP', None],
            'date_from'    : ['TIMESTAMP', None],
            'date_to'      : ['TIMESTAMP', None],
            'user'         : ['LOGIN', ''],
            'today'        : ['TIMESTAMP', 0],
            'id'           : ['LID', 0],
        }
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##


def _make_page_default(**kw):
    refer_id = int(kw.get('refer_id') or 0)
    mode = kw.get('mode')

    # -------------------
    # Page view rendering
    # -------------------

    args = _get_page_args()

    requested_dates = ''

    page = PageCenter(default_page, default_template, database_config)
    page._init_state(g.engine, args)

    page.desc_orders = (1,4,6,9,11,12,14,16,17)

    page.render(**kw)

    # ===================
    # View Data selection
    # ===================

    action = url_for('center.start')

    link = '%s'*7 % (
        page.base, 
        page.get_current_filter(),
        page.get_search(),
        page.get_selected_date(),
        page.get_current_sort(),
        page.get_selected_division(),
        page.get_selected_line(),
        )
    
    dates = page.ref_messages_dates()

    # ===================
    # Response processing
    # ===================

    page_title = '%s %s' % (default_title, Capitalize(mode))

    msg = (maketext('Center messages for period'), maketext('Logs For the date'))

    log_title = (requested_dates == '*') and '%s %s : %s' % (msg[0], min(dates), max(dates)) or \
        page.selected_date and '%s %s' % (msg[1], page.selected_date) or ''

    data_title = '%s%s' % ('', page.has_filter and ' %s [%s]' % (
        maketext('Center Messages List'), (
            page.shown_filter or '...'
        )) or maketext('Center Tab Connection Messages Title'))

    kw = page.run(page_title, data_title, action, link, **kw)

    response = page.response()
    response['pagination']['today'] = None
    
    kw.update(response)
    
    kw.update({
        'args'      : args,
        'divisions' : page.ref_divisions(),
        'lines'     : page.ref_lines(),
        'dates'     : dates,
    })

    kw['style']['show_scroller'] = 1

    return kw


@center.route('/', methods=['GET', 'POST'])
@center.route('/index', methods=['GET', 'POST'])
@login_required
def start():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()

        g.app_logger('%s.index' % default_page, maketext('Application error. See traceback.log for details'), is_error=True)

        raise


def index():
    mode = default_page
    debug, kw = init_response('%s %s' % (default_title, Capitalize(mode)), default_page)
    kw['product_version'] = product_version
    kw['mode'] = mode

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, refer_id:%s' % (
            command,
            kw.get('refer_id'),
        ))

    refresh()

    errors = []

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(**kw)

        if IsTrace:
            print_to(errorlog, '--> %s:%s %s %s' % (default_page, command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        raise

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('center.html', debug=debug, **kw))


@center.after_request
def make_response_no_cached(response):
    try:
        if g.engine is not None:
            g.engine.close()
    except:
        pass
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response


## ==================================================== ##


@center.route('/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    try:
        return loader_start()
    except:
        if IsPrintExceptions:
            print_exception()

        g.app_logger('%s.loader' % default_page, maketext('Application error. See traceback.log for details'), is_error=True)

        raise


def loader_start():
    exchange_error = ''
    exchange_message = ''

    is_extra = has_request_item(EXTRA_)

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    refer_id = get_request_item('refer_id') or '0'
    row_id = get_request_item('row_id') or '0'
    group = get_request_item('group') or None
    mode = get_request_item('mode') or None

    params = get_request_item('params') or None

    refresh(refer_id=refer_id)

    page = PageCenter(default_page, default_template, database_config)
    page._init_state(g.engine)

    if IsDeepDebug:
        print('--> action:%s refer_id:%s params:%s' % (action, refer_id, params))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s]%s' % (
                 action, 
                 g.current_user.login, 
                 refer_id, 
                 selected_menu_action,
                 params and ' params:[%s]' % params or '',
            ))

    currentfile = None
    sublines = []
    config = None

    data = ''
    number = ''
    columns = []
    total = 0
    status = ''
    path = None

    props = None
    errors = None

    tabs = _check_extra_tabs(g.requested_object)

    try:
        if action == default_action:
            #
            #   Defaul page action
            #
            action = _valid_extra_action(selected_menu_action) or default_log_action

        if not action:
            pass

        elif action == '801':
            pass

        elif action == '802':
            pass

        elif action == '803':
            pass

        elif action == '804':
            pass

        elif action == '805':
            pass

    except:
        print_exception()

    response.update({
        'action'           : action,
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error,
        'exchange_message' : exchange_message,
        # -----------------------------
        # Results (Log page parameters)
        # -----------------------------
        'refer_id'         : refer_id,
        'batch_id'         : '',
        # ----------------------------------------------
        # Default Lines List (sublines equal as batches)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : sublines,
        'config'           : config,
        'tabs'             : list(tabs.keys()),
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : total or len(data),
        'data'             : data,
        'status'           : status,
        'path'             : path,
        'props'            : props,
        'columns'          : columns,
        'errors'           : errors,
    })

    return jsonify(response)


