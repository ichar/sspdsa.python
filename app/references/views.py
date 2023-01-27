# -*- coding: utf-8 -*-

import re

from operator import itemgetter

from config import (
     CONNECTION, CONFIG_PATH,
     LocalDebug,
     )

from . import references

from .page_default import PageRender

from ..settings import *
from ..sockets import Commander
from ..database import database_config, DatabaseEngine
from ..utils import getToday, getDate, daydelta, checkPaginationRange, reprSortedDict

from app.semaphore.views import initDefaultSemaphore


##  ======================
##  App References Package
##  ======================


default_page = 'references'
default_action = '500'
default_log_action = '501'
default_template = 'refers'
default_title = 'Application References'

IsLocalDebug = LocalDebug[default_page]

default_date_format = DEFAULT_DATE_FORMAT[1]

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

def _check_extra_tabs(row):
    tabs = {}
    return tabs

def _valid_extra_action(action, row=None):
    return action

def _get_page_args():
    args = {}

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

def _make_page_default(**kw):

    # -------------------
    # Page view rendering
    # -------------------

    args = _get_page_args()

    page = PageRender(default_page, default_template, database_config)
    page._init_state(g.engine, args=args)

    # ===================
    # Response processing
    # ===================

    kw.update(page.run(page_title=maketext('%s Page' % default_title), **kw))

    return kw


@references.route('/', methods=['GET', 'POST'])
@references.route('/index', methods=['GET', 'POST'])
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
        print('--> command:%s, refer_id:%s, mode:%s' % (
            command,
            kw.get('refer_id'),
            kw.get('mode')
        ))

    refresh()

    errors = []

    kw['per_page'] = 0 # All data to page, no paging (default, monopage)

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(**kw)

        if IsTrace:
            print_to(errorlog, '--> %s:%s %s %s' % (default_page, command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        print_exception()

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('references.html', debug=debug, **kw))


@references.after_request
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


@references.route('/loader', methods = ['GET', 'POST'])
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

    refer_id = int(get_request_item('refer_id') or '0')
    row_id = get_request_item('row_id') or ''
    group = get_request_item('group') or None
    mode = get_request_item('mode') or None
    command = get_request_item('command') or None

    params = get_request_item('params') or {}

    refresh(refer_id=refer_id)

    page = PageRender(default_page, default_template, database_config)
    page._init_state(g.engine)

    if IsDeepDebug:
        print('--> action:%s refer_id:%s mode:%s' % (action, refer_id, mode))

    if IsTrace:
        print_to(errorlog, '--> references.loader:%s %s command:%s [%s:%s:%s:%s] params:%s engine:%s' % (
                 action, 
                 g.current_user.login, 
                 command,
                 refer_id, 
                 row_id,
                 mode, 
                 selected_menu_action,
                 params and (' params:%s' % reprSortedDict(params, is_sort=True)) or '',
                 repr(g.engine),
            ))

    config = None
    columns = []
    
    currentfile = None
    sublines = None
    data = {}
    number = ''
    total = 0
    status = ''
    path = None

    props = {}
    errors = None

    page_title = None
    data_title = None
    kw = {}
    is_error = 0

    tabs = _check_extra_tabs(g.requested_object)

    try:
        if action == default_action:
            #
            #   Defaul page action
            #
            action = _valid_extra_action(selected_menu_action) or None

        if not action:
            pass

        elif action == default_log_action:
            pass

        elif action == '502':
            #
            #   Object Sequence.nextval (pk)
            #
            mode = params.get('mode')
            if mode == 'messagetype':
                page.make_messagetypes(page_title, data_title, kw)
                view = page.messagetypes
            elif mode == 'node':
                page.make_nodes(page_title, data_title, kw)
                view = page.nodes
            else:
                is_error = 9
            pk = view.next_pk()
            data['mode'] = mode
            data['id'] = params.get('id')
            data['pk'] = pk

        elif action == '503':
            #
            #   Save Object item (create or update)
            #
            group = params.get('group')
            mode = params.get('mode')
            command = params.get('command')
            row_id = params.get('row_id')
            page_title = None
            data_title = None
            kw = {'id' : params.get('id')}
            is_error = 0
            if mode == 'messagetype':
                kw['messagetype_id'] = refer_id
                page.make_messagetypes(page_title, data_title, kw)
                view = page.messagetypes
            elif mode == 'node':
                kw['node_id'] = refer_id
                page.make_nodes(page_title, data_title, kw)
                view = page.nodes
            else:
                is_error = 9
            if not is_error:
                is_error, errors = view.save(command, params)
            if mode == 'messagetype':
                page.make_messagetypes(page_title, data_title, kw, with_make=True)
            elif mode == 'node':
                page.make_nodes(page_title, data_title, kw, with_make=True)
            data = kw.get(mode)
            config = data.get('config')
            columns = data.get('columns')
            total = data.get('total_rows')
            rows = data.get('rows')
            props['show_notification'] = 1
            if is_error:
                message = g.maketext('Error during %s data %sing' % (mode, command[0:-1]))
            else:
                message = g.maketext('Successfully %s data %sed' % (mode, command[0:-1]))
            if not g.system_config.ShowSuccessNotification:
                props['show_notification'] = 0
            props['group'] = group
            props['mode'] = mode
            props['message'] = errors and '<br>'.join(errors) or message
            props['is_error'] = is_error
            props['row_id'] = kw[mode].get('pagination').get('selected')[0] #row_id
            props['refer_id'] = refer_id
            props['total'] = total
            data = rows

        elif action == '504':
            #
            #   Context menu item activated
            #
            menu_id = params.get('menu_id')
            props = params
            props['OK'] = 0
            is_error = False
            props['show_notification'] = 1
            commander = Commander()
            if commander.sync_references(menu_id):
                props['OK'] = 1
                props['Error'] = 0
            else:
                is_error = commander.is_error
                props['Error'] = is_error
            unit = commander.node
            if is_error:
                message = '%s<br>%s<br>%s' % (g.maketext('Error during socket-command running'), menu_id, unit)
            else:
                message = '%s<br>%s<br>%s' % (g.maketext('Socket Command is successfully done'), menu_id, unit)

            props['message'] = is_error and '<br>'.join(commander.errors) or message
            props['unit'] = unit

            commander = None

            if not g.system_config.ShowSuccessNotification:
                props['show_notification'] = 0
            print_to(None, props)


        elif action == '505':
            pass

    except:
        print_exception()

    page = None

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
        'row_id'           : row_id,
        'mode'             : mode,
        # ----------------------------------------------
        # Default Lines List (sublines equal as params)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : sublines,
        'config'           : config,
        'tabs'             : list(tabs.keys()),
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : total or data and isIterable(data) and len(data) or isinstance(data, dict) and 1 or 0,
        'data'             : data,
        'status'           : status,
        'path'             : path,
        'props'            : props,
        'columns'          : columns,
        'errors'           : errors,
    })

    current_app.json_encoder = DataEncoder
    return jsonify(response)
