# -*- coding: utf-8 -*-

import re
from operator import itemgetter

from config import (
     CONNECTION, CONFIG_PATH,
     LocalDebug,
     )

from . import main

from ..settings import *
from ..pages import ViewRender
from ..sockets import Commander
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, Capitalize,
     checkPaginationRange,
     daydelta
     )

from .. import db

from .page_equipment import PageEquipment


##  ===================
##  Main Viewer Package
##  ===================


default_page = 'main'
default_action = '700'
default_log_action = '701'
default_template = 'main'
default_title = 'Application Main'

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

def _valid_extra_action(action, row=None):
    return action

def _get_page_args():
    args = {}

    try:
        args = { \
            'division'     : ['DIVISION', int(get_request_item('division') or 0)],
            'line'         : ['LINE', int(get_request_item('line') or 0)],
            'selected_date': ['TIMESTAMP', get_request_item('selected_date') or None],
            'date_from'    : ['TIMESTAMP', get_request_item('date_from') or None],
            'date_to'      : ['TIMESTAMP', get_request_item('date_to') or None],
            'user'         : ['LOGIN', get_request_item('user') or ''],
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
            'id'           : ['LID', 0],
        }
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##


def _make_page_default(**kw):
    mode = kw.get('mode') or 'default'
    change_id = int(kw.get('change_id') or 0)

    # -------------------
    # Page view rendering
    # -------------------

    args = _get_page_args()

    page = PageEquipment(default_page, default_template, database_config)
    page._init_state(g.engine, args)

    page.render(**kw)

    # ===================
    # View Data selection
    # ===================

    action = url_for('main.start', mode='equipment')

    link = '%s'*7 % (
        page.base, 
        page.get_current_filter(),
        page.get_search(),
        page.get_selected_date(),
        page.get_current_sort(),
        page.get_selected_division(),
        page.get_selected_line(),
        )

    # ===================
    # Response processing
    # ===================

    data_title = page.has_filter and ' %s [%s]' % (
        maketext('Equipment Diagram for'), (page.shown_filter or '...')) or \
        maketext('Main Equipment Diagram')

    kw.update(page.run(page_title=maketext('%s %s Page' % (default_title, Capitalize(mode))), data_title=data_title, **kw))

    kw.update({
        'args'      : args,
        'divisions' : page.ref_divisions(),
        'lines'     : page.ref_lines(),
        'dates'     : page.ref_activity_dates(),
        
    })

    kw['diagram_forced_refresh_timeout'] = connection_params.forced_refresh_timeout
    kw['style']['show_scroller'] = 1

    return kw


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        pass #abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/restart')
def server_restart():
    from manage import manager, start
    shutdown = request.environ.get('werkzeug.server.shutdown')
    shutdown()
    start()


@main.route('/', methods=['GET'])
def default_route():
    url = url_for('main.start', mode='equipment')
    return redirect(url)


@main.route('/index', methods=['GET', 'POST'])
@main.route('/index/<mode>', methods=['GET', 'POST'], defaults={'mode': None})
@main.route('/equipment', methods=['GET', 'POST'])
@login_required
def start(mode=None):
    try:
        if mode is not None:
            return redirect(url_for('main.start', mode=mode))
        elif mode == 'center':
            return redirect(url_for('center.start'))
        elif mode == 'branch':
            return redirect(url_for('branch.start'))
        else:
            return index('equipment')
    except:
        if IsPrintExceptions:
            print_exception()


def index(mode):
    debug, kw = init_response('%s %s' % (default_title, Capitalize(mode)), default_page)
    kw['product_version'] = product_version
    kw['mode'] = mode

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, mode:%s, command:%s' % (
            command,
            mode,
            command
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
            print_to(errorlog, '--> main:%s command:%s login:%s' % (mode, command, current_user.login), request=request)
    except:
        if IsPrintExceptions:
            print_exception()

    if command and command.startswith('admin'):
        pass

    template = '%s.html' % mode

    return make_response(render_template(template, debug=debug, **kw))


@main.after_request
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


@main.route('/loader', methods = ['GET', 'POST'])
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

    page = PageEquipment(default_page, default_template, database_config)
    page._init_state(g.engine)

    if IsDeepDebug:
        print('--> action:%s refer_id:%s row_id:%s' % (action, refer_id, row_id))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s:%s]%s' % (
                 action, 
                 g.current_user.login, 
                 refer_id, 
                 row_id, 
                 mode, 
                 selected_menu_action,
                 params and ' params:[%s]' % params or '',
            ))

    config = page.get_config()
    columns = page.get_view_columns()

    currentfile = None
    sublines = []

    data = {}
    number = ''
    total = 0
    status = ''
    path = None

    props = {}
    errors = None
    
    page_title = None
    data_title = None

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
            #
            #   Diagram Refresh with State updating
            #
            is_forced_refresh = get_request_item('forced_refresh') or None
            is_done, is_error, errors = page.forced_refresh()
            props = page.render_diagram()
            if is_forced_refresh and is_done:
                props['flash_message'] = g.maketext('State of node was forced updated!')
                props['with_beep'] = g.system_config.IsWithBeep
            props['is_error'] = is_error
            props['errors'] = is_error and '<br>'.join(errors) or None
            mode = 'diagram'

        elif action == '702':
            #
            #   Tabline Upload [mode]
            #
            row_id = params.get('id')
            kw = {}
            is_error = 0
            if group == 'activities':
                page.make_activities(page_title, data_title, kw, params=params)
                data = page._activities.response.get('rows')
            elif group == 'reliabilities':
                page.make_reliabilities(page_title, data_title, kw, params=params)
                data = page._reliabilities.response.get('rows')

            data = kw.get(group)
            config = data.get('config')
            columns = data.get('columns')
            total = data.get('total_rows')
            rows = data.get('rows')
            props['group'] = group
            props['mode'] = mode
            props['row_id'] = kw[group].get('pagination').get('selected')[0] #row_id
            props['refer_id'] = refer_id
            props['total'] = kw[group].get('pagination').get('total')
            chunk = params.get('next_chunk')
            props['chunk'] = chunk and [int(chunk[0]), int(chunk[1])] or [0, 0]
            props['next_row'] = int(params.get('next_row'))
            data = rows

        elif action == '703':
            #
            #   Context menu item activated
            #
            menu_id = params.get('menu_id')
            unit = params.get('unit')
            props = params
            props['OK'] = 0
            is_error = False
            props['show_notification'] = 1
            commander = Commander()
            if commander.main(menu_id, unit):
                props['OK'] = 1
                props['Error'] = 0
            else:
                is_error = commander.is_error
                props['Error'] = is_error
            if is_error:
                message = '%s<br>%s<br>%s' % (g.maketext('Error during socket-command running'), menu_id, unit)
            else:
                message = '%s<br>%s<br>%s' % (g.maketext('Socket Command is successfully done'), menu_id, unit)

            props['message'] = is_error and '<br>'.join(commander.errors) or message

            commander = None

            if not g.system_config.ShowSuccessNotification:
                props['show_notification'] = 0

        elif action == '704':
            pass

        elif action == '705':
            pass

    except:
        if IsPrintExceptions:
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
        # -----------------------------
        # Default Lines List (sublines)
        # -----------------------------
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
