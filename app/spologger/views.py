# -*- coding: utf-8 -*-

import math
from operator import itemgetter

from config import (
     CONNECTION,
     LocalDebug
     )

from . import spolog

from ..settings import *
from ..models import get_users_dict
from ..pages import ViewRender
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, daydelta
     )

from ..worker import SpoGenerator


##  ==================
##  SPO Logger Package
##  ==================


default_page = 'spologviewer'
default_action = '600'
default_log_action = '601'
default_template = 'spologs'
default_title = 'Application Special Logs'


log_config = {
    'root'      : './logspo',
    'name'      : '',
    'dir'       : ('.*',),
    'file'      : ('(\d{2}-\d{2}-\d{4})\.log',),
    'error'     : 'ERROR',
    'suspend' : (
        ),
    'errorlog'  : 'mod-traceback-%(now)s-%(page)s.log',
    'delimeter' : " : "
}

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

def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

def _get_page_args():
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    try:
        args = { \
            'status'       : ['STATUS', int(get_request_item('status') or 0)],
            'selected_date': ['TIMESTAMP', get_request_item('selected_date') or None],
            'date_from'    : ['TIMESTAMP', get_request_item('date_from') or None],
            'date_to'      : ['TIMESTAMP', get_request_item('date_to') or None],
            'yesterday'    : ['TIMESTAMP', get_request_item('yesterday', check_int=1) or 0],
            'tomorrow'     : ['TIMESTAMP', get_request_item('tomorrow', check_int=1) or 0],
            'today'        : ['TIMESTAMP', get_request_item('today', check_int=1) or 0],
            'user'         : ['LOGIN', get_request_item('user') or ''],
            'id'           : ['LID', int(get_request_item('_id') or '0')],
        }
    except:
        args = { \
            'status'       : ['STATUS', 0],
            'selected_date': ['TIMESTAMP', None],
            'date_from'    : ['TIMESTAMP', None],
            'date_to'      : ['TIMESTAMP', None],
            'yesterday'    : ['TIMESTAMP', 0],
            'tomorrow'     : ['TIMESTAMP', 0],
            'today'        : ['TIMESTAMP', 0],
            'user'         : ['LOGIN', ''],
            'id'           : ['LID', 0],
        }
        flash('Please, update the page by Ctrl-F5!')

    return args

## ==================================================== ##

def _make_page_default(kw):
    log_id = int(kw.get('log_id') or 0)

    # -------------------
    # Page view rendering
    # -------------------

    args = _get_page_args()

    page = ViewRender(default_page, default_template, database_config)
    page._init_state(g.engine, args)

    page.set_current_file({
        'id'       :'logger', 
        'name'     :'logger',
        'disabled' : '',
        'value'    : '',
    })

    page.desc_orders = (1,5,)
    page.with_chunks = 0

    page.render(**kw)

    # ===================
    # View Data selection
    # ===================

    id_column = 'np'
    name_column = 'TIMESTAMP'
    line = 0

    requested_dates = page.requested_dates
    sort_type = 'reverse'

    lines = []

    generator = SpoGenerator(page.view, page=default_page, config=log_config)
    generator._init_state(requested_dates, sort_type=sort_type)
    generator.per_page = 100
    
    page.before(id_column, name_column, log_id, **kw)

    if generator.is_valid():
        #lines = generator.get_lines(status=page.selected_status, user=page.selected_user, search=page.search)

        for row in generator.get_line(status=page.selected_status, user=page.selected_user, search=page.search):
            page.row_iter(row)

        page.row_finish()

    if not lines and page.rows:
        lines = ['%s<br>' % generator.row_to_line(row) for row in page.rows]

    dates = generator.dates
    files = generator.files_showname
    selected_date = page.date_from or generator.selected_date

    # ===================
    # Response processing
    # ===================

    page.after()

    log_title = (page.date_from and page.date_to) and '%s %s : %s' % (maketext('Logs for period'), page.date_from, page.date_to) or \
        (requested_dates == '*') and  '%s %s : %s' % (maketext('Logs for period'), min(dates), max(dates)) or \
        '%s %s' % (maketext('Logs For the date'), generator.selected_date)

    data_title = '%s%s' % (log_title, page.has_filter and ' %s: %s' % (
        maketext('Log Events Information'), (
            page.filter or '...'
        )) or '')

    link = '%s%s%s%s%s%s%s%s' % (
        page.base, 
        page.get_current_filter(),
        page.get_search(),
        page.get_date_from(),
        page.get_current_sort(),
        page.get_selected_status(),
        page.get_selected_user(),
        page.get_state(),
        )

    kw.update(page.response(
        title='%s Page' % default_title,
        data_title=data_title, 
        total_selected=0,
        action=url_for('spologviewer.start'),
        link=link,
        params=[]
    ))

    kw.update({
        'statuses'          : page.statuses,
        'users'             : page.users,
        'search'            : page.search or '',
        'lines'             : lines, 
        'dates'             : dates,
        'files'             : files,
        'selected_date'     : selected_date,
        'selected_user'     : page.selected_user,
    })

    kw['style']['show_scroller'] = 1

    return kw


@spolog.route('/', methods=['GET', 'POST'])
@spolog.route('/index', methods=['GET', 'POST'])
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
    debug, kw = init_response(default_title, default_page)
    kw['product_version'] = product_version

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, log_id:%s' % (
            command,
            kw.get('log_id'),
        ))

    refresh()

    errors = []

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> %s:%s %s %s' % (default_page, command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        raise

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('spologger.html', debug=debug, **kw))


@spolog.after_request
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


@spolog.route('/loader', methods = ['GET', 'POST'])
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

    log_id = int(get_request_item('log_id') or '0')
    params = get_request_item('params') or None

    refresh(log_id=log_id)

    page = ViewRender(default_page, default_template, database_config)

    if IsDeepDebug:
        print('--> action:%s log_id:%s params:%s' % (action, log_id, params))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s]%s' % (
                 action, 
                 g.current_user.login, 
                 log_id, 
                 selected_menu_action,
                 params and ' params:[%s]' % params or '',
            ))

    config = page.get_config()
    columns = page.get_view_columns()

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

        elif action == default_log_action:
            pass

        elif action == '602':
            pass

        elif action == '603':
            pass

        elif action == '604':
            pass

        elif action == '605':
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
        'log_id'           : log_id,
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


