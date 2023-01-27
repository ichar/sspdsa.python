# -*- coding: utf-8 -*-

import re
from operator import itemgetter

from config import (
     CONNECTION, CONFIG_PATH,
     LocalDebug,
     )

from . import maintenance

from ..settings import *
from ..pages import ViewRender
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate,
     checkPaginationRange,
     daydelta
     )

from .. import db

##  ========================
##  Обслуживание БД СПО КПТС
##  ========================

default_page = 'maintenance'
default_action = '900'
default_log_action = '901'
default_template = 'maintenance'
default_title = 'Application Database Maintenance'

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

def _check_extra_tabs(row):
    tabs = {}
    return tabs


def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset


def _get_page_args():
    args = {}

    try:
        args = { \
            'client'    : ('ClientID', int(get_request_item('client') or '0')),
        }
    except:
        args = { \
            'client'    : ('ClientID', 0),
        }
        flash('Please, update the page by Ctrl-F5!')

    return args

## ==================================================== ##

def _make_page_default(**kw):
    change_id = int(kw.get('change_id') or 0)

    is_admin = current_user.is_administrator()

    # -----------------------
    # Представление БД (view)
    # -----------------------

    args = _get_page_args()

    page = ViewRender(default_page, default_template, database_config)
    page._init_state(g.engine, args)
    
    page.render(**kw)

    # ==========================
    # >>> Выборка данных журнала
    # ==========================

    id_column = 'ID'
    name_column = 'TIMESTAMP'

    page.before(id_column, name_column, change_id, **kw)

    if g.engine != None:
        pass

    # =================
    # >>> Постобработка
    # =================

    page.after()

    data_title = ''

    kw.update(page.response(
        title='%s Page' % default_title,
        data_title=data_title, 
        action=url_for('maintenance.start'),
        link=None,
    ))

    kw['style']['show_scroller'] = 1

    return kw

@maintenance.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@maintenance.route('/', methods=['GET', 'POST'])
@maintenance.route('/index', methods=['GET', 'POST'])
@login_required
def start():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()


def index():
    debug, kw = init_response(default_title, default_page)
    kw['product_version'] = product_version

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, file_id:%s, batch_id:%s' % (
            command,
            kw.get('file_id'),
            kw.get('batch_id')
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
            print_to(errorlog, '--> maintenance:%s %s %s' % (command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        if IsPrintExceptions:
            print_exception()

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('maintenance.html', debug=debug, **kw))


@maintenance.after_request
def make_response_no_cached(response):
    try:
        if g.decoder is not None:
            g.decoder.flash()
        if g.engine is not None:
            g.engine.close()
    except:
        pass
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

## ==================================================== ##

@maintenance.route('/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    is_extra = has_request_item(EXTRA_)

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    file_id = int(get_request_item('file_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')
    batchtype = int(get_request_item('batchtype') or '0')
    batchstatus = int(get_request_item('batchstatus') or '0')
    params = get_request_item('params') or None

    refresh(file_id=file_id)

    page = ViewRender(default_page, default_template, database_config)

    if IsDeepDebug:
        print('--> action:%s file_id:%s batch_id:%s batchtype:%s batchstatus:%s' % (action, file_id, batch_id, batchtype, batchstatus))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s:%s:%s]%s' % (
                 action, 
                 g.current_user.login, 
                 file_id, batch_id, 
                 batchtype, 
                 batchstatus, 
                 selected_menu_action,
                 params and ' params:[%s]' % params or '',
            ))

    config = page.get_config()
    columns = page.get_view_columns()

    currentfile = None
    batches = []
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
            action = selected_menu_action

        if not action:
            pass

        elif action == '901':
            pass

        elif action == '902':
            pass

        elif action == '903':
            pass

        elif action == '904':
            pass

        elif action == '905':
            pass

    except:
        if IsPrintExceptions:
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
        'file_id'          : file_id,
        'batch_id'         : batch_id,
        # ----------------------------------------------
        # Default Lines List (sublines equal as batches)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : batches,
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



