# -*- coding: utf-8 -*-

import re
import sys
from operator import itemgetter

from config import (
     UTC_EASY_TIMESTAMP, CONNECTION, CONFIG_PATH, 
     LocalDebug,
     )

from . import configurator

from ..models import (
       ConfigChange, registerConfigChange, deleteConfigChange, get_users_dict
       )

from ..settings import *
from ..pages import ViewRender
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, daydelta,
     checkPaginationRange, reprSortedDict
     )


##  =====================
##  App Configurator Page
##  =====================


default_page = 'configurator'
default_action = '400'
default_log_action = '401'
default_template = 'configs'
default_title = 'Application Configurator'

IsLocalDebug = LocalDebug[default_page]

xrec = re.compile('(\s*?([\*\#].+?)\n)')
xrep = re.compile('(([^\*\#]\w+?)=(.*))')
#xre = re.compile('((\s*?[\*\#].+?\n)([^\*\#]\w+?)=(.*))')

config_path = CONFIG_PATH


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
    default_date_format = DEFAULT_DATE_FORMAT[1]
    return getDate(getToday(), default_date_format)

def _check_extra_tabs(row):
    return {}

def _valid_extra_action(action, row=None):
    return action

def _get_page_args():
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    try:
        args = { \
            'status'       : ['STATUS', int(get_request_item('status') or 0)],
            'selected_date': ['TIMESTAMP', get_request_item('selected_date') or None],
            'date_from'    : ['RegisterDate', get_request_item('date_from') or None],
            'date_to'      : ['RegisterDate', get_request_item('date_to') or None],
            'yesterday'    : ['RegisterDate', get_request_item('yesterday', check_int=1) or 0],
            'tomorrow'     : ['RegisterDate', get_request_item('tomorrow', check_int=1) or 0],
            'today'        : ['RegisterDate', get_request_item('today', check_int=1) or 0],
            'user'         : ['User', get_request_item('user') or ''],
            'id'           : ['FileID', int(get_request_item('_id') or '0')],
        }
    except:
        args = { \
            'status'       : ['STATUS', 0],
            'selected_date': ['TIMESTAMP', None],
            'date_from'    : ['RegisterDate', None],
            'date_to'      : ['RegisterDate', None],
            'yesterday'    : ['RegisterDate', 0],
            'tomorrow'     : ['RegisterDate', 0],
            'today'        : ['RegisterDate', 0],
            'user'         : ['User', ''],
            'id'           : ['FileID', 0],
        }
        flash('Please, update the page by Ctrl-F5!')

    return args


def _open_config(mode):
    return open(config_path, mode)

def _check_params(lines, with_content=None, with_decode=None):
    """
        Check and collect params from config body
        
        Arguments:
            lines        -- list of content lines, used for parsing data from file and frontside
            with_content -- flag, return string content body also
            with_decode  -- flag, use decoding from binary
        
        Returns:
            params       -- dict, found params values
            content      -- str, config body
    """
    params = {}
    content= ''
    c = ''
    for line in lines:
        s = with_decode and line.decode() or line
        if with_content:
            content += s
        m = re.match(xrec, s)
        if m is not None:
            c = m.group(2).strip()
            continue
        m = re.match(xrep, s)
        p = v = ''
        if m is not None:
            p = m.group(2).strip()
            v = m.group(3).strip()
            if p not in params:
                params[p] = (v, c)
                c = ''

    if with_content:
        return params, content
    else:
        return params


def _get_rows(page, **kw):
    """
        Get ConfigChange rows from the database
    """
    rows = []

    change_id = int(kw.get('change_id') or 0)
    state = page.state
    view = page.view

    id_column = 'ID'
    name_column = 'TIMESTAMP'

    page.before(id_column, name_column, change_id, **kw)

    page.per_page = kw.get('per_page') or 0

    if g.engine != None:
        rows = ConfigChange.get_rows(view)
        
        for row in rows:
            row['TIMESTAMP'] = getDate(row['TIMESTAMP'], UTC_EASY_TIMESTAMP)

            page.row_iter(row)

        page.row_finish()

    page.after()

    return rows

def _get_changes(change_id, **kw):
    """
        Get ConfigChange by the given id
        
        Arguments:
            change_id -- int, row id

        Keywords arguments:
            view      -- dict, current database config
            
        Returns:
            row -- dict
    """
    view = kw.get('view') or database_config[default_template]
    
    rows = ConfigChange.get_rows(view, id=change_id)

    return rows

def _make_changes(page, command, content, **kw):
    """
        Compare and register params changes
        
        Arguments:
            command -- str, save|restore
            content -- str, body content with changes from frontside

        Keywords arguments:
            view      -- dict, current database config
        
        Returns:
            data    -- dict, table of rows
            columns -- list of dict, columns for table viewer
            prop    -- dict, any properties for handler
                selected_row -- dict, selected table row
                css: -- list: classes for html-controls
    """
    data, props, css = {}, {}, {}

    g.app_logger('%s._make_changes' % default_page, g.maketext('Configurator changes activated'), is_info=True)

    #view = kw.get('view') or database_config[default_template]
    columns = page.get_view_columns()

    def _item(p, v, c):
        return '%s\n%s=%s' % (c, p, v)

    config_file = _open_config('rb')

    params_before = _check_params(config_file.readlines(), with_decode=True)

    config_file.close()

    lines = content.split('\n')
    params_after = _check_params(lines)

    before = []
    after = []

    for p in params_before.keys():
        if params_after[p][0] != params_before[p][0]:
            c = params_before[p][1]
            v = params_before[p][0]
            before.append(_item(p, v, c))
            v = params_after[p][0]
            after.append(_item(p, v, c))

    props = {'before': '\n'.join(before), 'after': '\n'.join(after)}

    IsOk = registerConfigChange(props, g.current_user.login)

    _set_config(lines)

    page.line = kw.get('line') or -1

    data = _get_rows(page)

    props.update({
        'selected_row' : page.selected_row,
        'css' : css,
    })

    return data, columns, props

def _set_config(lines):
    config_file = _open_config('wb')

    with config_file:
        for line in lines:
            w = ('%s\n' % line)
            config_file.write(w.encode())

    config_file.close()

def _get_config():
    config_file = _open_config('rb')

    messages = []
    if not config_file.closed:
        messages.append('>>> %s: <span class="high">%s</span>' % (maketext('Successfully opened config file'), config_path))

    params, content = _check_params(config_file.readlines(), with_content=True, with_decode=True)

    for n, p in enumerate(sorted(list(params.keys()))):
        messages.append('%s<br>%s. %s=<span class="high">%s</span>' % (params[p][1], n, p, params[p][0]))

    messages.append('>>> %s: <span class="high">%s</span>' % (maketext('Total found parameters'), len(params.keys())))

    config_file.close()

    messages.append('>>> %s' % maketext('File is closed'))
    
    return params, content, messages

## ==================================================== ##

def _make_page_default(kw):
    change_id = int(kw.get('change_id') or 0)

    # -------------------
    # Page view rendering
    # -------------------

    args = _get_page_args()

    page = ViewRender(default_page, default_template, database_config)
    page._init_state(g.engine, args)

    page.render(**kw)

    # ===================
    # View Data selection
    # ===================

    params, content, messages = _get_config()

    page.set_current_file({
        'id'       :'config', 
        'name'     :'param',
        'disabled' : '',
        'value'    : content,
    })

    rows = _get_rows(page, **kw)

    # ===================
    # Response processing
    # ===================

    data_title = ''

    kw.update(page.response(
        title='%s Page' % default_title,
        data_title=data_title, 
        action=url_for('configurator.start'),
        link=None,
    ))

    kw['messages'] = messages
    kw['style']['show_scroller'] = 1
    kw['messages_hidden'] = g.system_config.ConfigMessagesHidden and 'hidden' or ''

    return kw


@configurator.route('/', methods=['GET', 'POST'])
@configurator.route('/index', methods=['GET', 'POST'])
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
        print('--> command:%s, change_id:%s, param_id:%s' % (
            command,
            kw.get('change_id'),
            kw.get('param_id')
        ))

    refresh()

    errors = []

    kw['per_page'] = 0 # All data to page, no paging (default, monopage)

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> %s:%s %s keys:%s' % (default_page, command, current_user.login, 
                list(kw.get('current_file', {}).keys()),), request=request)
    except:
        print_exception()

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('configurator.html', debug=debug, **kw))


@configurator.after_request
def make_response_no_cached(response):
    try:
        if g.engine is not None:
            g.engine.close()
    except:
        pass
    if response is not None:
        # response.cache_control.no_store = True
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store'
        return response

## ==================================================== ##


@configurator.route('/loader', methods = ['GET', 'POST'])
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

    change_id = int(get_request_item('change_id') or '0')
    row_id = get_request_item('row_id') or ''
    group = get_request_item('group') or None
    mode = get_request_item('mode') or None
    command = get_request_item('command') or None
    content = get_request_item('content') or None

    params = get_request_item('params') or {}

    refresh(change_id=change_id)

    page = ViewRender(default_page, default_template, database_config)
    page._init_state(g.engine, None)

    if IsDeepDebug:
        print('--> action:%s change_id:%s row_id:%s content:%s' % (action, change_id, row_id, content and len(content)))

    if IsTrace:
        print_to(errorlog, '--> configurator.loader:%s %s command:%s [%s:%s:%s:%s] params:%s %s engine:%s' % (
                 action, 
                 g.current_user.login, 
                 command,
                 change_id, 
                 row_id,
                 mode, 
                 selected_menu_action,
                 params and (' params:%s' % reprSortedDict(params, is_sort=True)) or '',
                 content and 'content len:[%s]' % len(content) or '',
                 repr(g.engine),
            ))

    config = page.get_config()
    columns = page.get_view_columns()

    currentfile = None
    sublines = None
    data = None
    number = ''
    params = None
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
            action = _valid_extra_action(selected_menu_action) or None

        if not action:
            pass

        elif action == default_log_action:
            #
            #   Get changes item
            #
            changes = _get_changes(change_id, view=config)
            params, content, messages = _get_config()
            props = {
                'content'  : content,
                'params'   : params,
                'changes'  : changes,
            }

        elif action == '402':
            #
            #   Make changes item
            #
            sublines, columns, props = _make_changes(page, command, content, view=config, line=0)
            params, content, messages = _get_config()
            selected_row = props.get('selected_row')
            props['content'] = content
            props['change_id'] = change_id
            props['row_id'] = selected_row[0]
            props['group'] = group;
            props['mode'] = mode;
            data = sublines
            action = default_action

        elif action == '403':
            pass

        elif action == '404':
            pass

        elif action == '405':
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
        'change_id'        : change_id,
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

    return jsonify(response)
