# -*- coding: utf-8 -*-

import math
from operator import itemgetter

from config import IsTrace, isIterable, default_chunk

from .settings import *
from .models import (
     Division, Node, MessageType, Bind, Line, LineState, Message,
     registerDivision, registerNode, registerMessageType, registerBind, get_users_dict,
     gen_lines, gen_activities, gen_reliabilities, gen_center_exchange, gen_capacities, gen_speeds
     )
from .utils import (
     normpath, getToday, getDate, getDateOnly, checkDate, spent_time, makeSearchQuery, getString, getSQLString,
     Capitalize, unCapitalize, sortedDict, checkPaginationRange, sint
     )

from app.semaphore.views import initDefaultSemaphore

##  ===============================
##  Page request parsing Main Class
##  ===============================

default_date_format = DEFAULT_DATE_FORMAT[1]


def _today():
    return getDate(getToday(), default_date_format)

def clean(s):
    return s.replace('None', '...')

def check_int(x):
    v = 0
    if x is not None:
        v = int(x)
    else:
        v = x
    return v

def check_line(s):
    return s and clean(s.replace(':ЦУП-Е', ':КТС01'))

def get_line(node1, node2):
    return check_line('%s - %s' % (node1, node2))

def get_line_id(kuo, kuov):
    return clean('%s-%s' % (kuo, kuov))

def get_line_node1_name(line):
    return line.node1[0].pikts

def get_line_node2_name(line):
    return line.node1[1].pikts

def get_line_name(line):
    name = ''
    try:
        name = get_line(line.node1[0].kikts, line.node2[0].kikts)
    except:
        name = None
    return name

def get_line_fullname(line):
    name = ''
    try:
        name = get_line(line.node1[0].pikts, line.node2[0].pikts)
    except:
        name = None
    return name

def get_item_code(ob):
    return clean('%s_%s%s' % (ob.nsch, ob.nsch, ob.nkts))

def _check_extra_tabs(row):
    tabs = {}
    return tabs

def _get_top(per_page, page):
    """
        Pagination params calculation
       
        System config param:
            IsApplyOffset -- int(1|0) Use OFFSET in SQL-queries
       
        Arguments:
           per_page -- int, size of page
           page     -- int, number of page to select

        Returns:
           top      -- select top rows (ORM:limit)
           offset   -- skip offset rows from top (ORM:offset)
    """
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

def _evaluate_date(s, x, format=default_date_format):
    d = getDate(s, format, is_date=True)
    return d and getDate(daydelta(d, x), format)


## ==================================================== ##


class PageLocal:

    def __init__(self, **kwargs):
        if IsDeepDebug:
            print('PageLocal init')

        self._search = None

        self._selected_date = None
        self._selected_division = None
        self._selected_line = None

        self._local_node = None

        self.divisions = None
        self.nodes = None
        self.lines = None

        self.ordered_nodes = []
        self.ordered_lines = []

        self.source_divisions = []
        self.map_lines = {}

        self._filter_items = None

        self._args = {}

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageLocal initstate')

        self.engine = engine
        self._args = args
        self.factory = factory

        if self.engine is None:
            pass

        self._filter_items = {}

        self.set_local_node()

    @property
    def is_main(self):
        return connection_params.is_main
    @property
    def local_node(self):
        return self._local_node and self._local_node[0] or None
    @property
    def args(self):
        return self._args or {}
    @property
    def search(self):
        return self._search and self._search[0] or None
    @property
    def selected_date(self):
        return self._selected_date and self._selected_date[0] or None
    @selected_date.setter
    def selected_date(self, value):
        self._selected_date = value
    @property
    def selected_division(self):
        return self._selected_division and self._selected_division[0] or None
    @property
    def selected_line(self):
        return self._selected_line and self._selected_line[2] or None
    @property
    def filter_items(self):
        return self._filter_items
    @property
    def has_filter(self):
        return list(filter(None, [self._filter_items[key][0] for key in self._filter_items])) and 1 or 0
    @property
    def filter(self):
        return self.has_filter and ':'.join([str(self._filter_items[key][0]) 
            for key in self._filter_items
                if self._filter_items[key][0] is not None])
    @property
    def shown_filter(self):
        items = self._filter_items
        shown = items and ', '.join(['%s:%s' % (g.maketext(items.get(key)[1]), str(items[key][0][1])) 
            for key in items 
                if items.get(key) is not None and items[key][0] is not None])
        return shown
    @property
    def query(self):
        if self.has_filter:
            items = self._filter_items
            args = {}
            args['local_node'] = 'local_node' in items and self.local_node
            args['selected_date'] = 'selected_date' in items and self.selected_date
            args['selected_line'] = 'selected_line' in items and self.selected_line
            args['selected_division'] = 'selected_division' in items and self.selected_division
            args['search'] = 'search' in items and self.search
            return args
        return None

    @property
    def is_valid(self):
        return True

    #   ------------
    #   PAGE FILTERS
    #   ------------

    def set_search(self):
        search = get_request_search() or None
        self._search = search and (search, search) or None

    def set_selected_date(self):
        date = self._args.get('selected_date') or None
        value = date and getDate(date[1], format=LOCAL_EASY_DATESTAMP, is_date=True) and date[1] or None
        self._selected_date = value and (date[1], value) or None

    def set_selected_division(self):
        self._selected_division = None
        division = self._args.get('division')
        if division and division[1] > 0:
            _id = division[1] - 1
            ob = self.source_divisions.get(_id)
            if ob is not None:
                self._selected_division = (ob['ID'], '%s-%s' % (ob['NAME'], ob['UNIT']))

    def set_selected_line(self):
        self._selected_line = None
        line_id = self._args.get('line') and self._args['line'][1] or None
        if line_id is None:
            return
        _id = int(line_id)
        for line in self.ordered_lines:
            if line.ksd == _id:
                nodes = line.kuo or 0, line.kuov or 0
                code = get_line_id(nodes[0], nodes[1])
                name = get_line_name(line)
                self._selected_line = (_id, name, nodes)
                break

    def get_search(self):
        return self._search and ("&search=%s" % self.search) or ''

    def get_selected_date(self):
        return self._selected_date and ("&selected_date=%s" % self.selected_date) or ''

    def get_selected_division(self):
        return self._selected_division is not None and ("&division=%s" % self.selected_division) or ''

    def get_selected_line(self):
        return self._selected_line and ("&line=%s" % self.selected_line[0]) or ''

    #   ----------
    #   MODEL DATA
    #   ----------

    def get_items(self, cls, key):
        source = cls.ordered_rows()
        rows = cls.get_rows(self.database_config.get(key), obs=source)
        return dict([(x['ID'], x) for x in rows]), source

    def set_local_node(self):
        local_node = connection_params.local_node
        row = Node.get_local_node(local_node)
        if row is not None and row.kuo:
            self._local_node = (str(row.kuo), row.kikts, row.pikts)
        else:
            self._local_node = None

    #   ----------
    #   REFERENCES
    #   ----------

    def ref_divisions(self):
        items = []
        vch = '%s ' % g.maketext('vch')
        if g.system_config.UseRefDivisionUnits:
            rows = Division.get_rows(database_config.get('divisions'), obs=Division.divisions())
            items += [[int(x['ID']), '%s[ %s%s ]' % (x['NAME'], x['UNIT'].isdigit() and vch or '', x['UNIT'])] for x in rows]
        else:
            rows = Division.divisions()
            items += [[int(x.nsch), '%s[ %s%s ]' %  (x.isch, x.vch.isdigit() and vch or '', x.vch)] for x in rows]
        for item in items:
            item[0] += 1
        #items = sorted(items, key=itemgetter(1))
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        if g.system_config.UseRefEmptyValue:
            items.insert(1, (-1, EMPTY_REFERENCE_VALUE,))
        return items

    def ref_lines(self):
        args = None
        node = None
        if self.local_node is not None and not self.is_main:
            node = self.filter_items.get('local_node') and self.local_node or None
        items = []
        if g.system_config.UseRefLineUnits == 1:
            lines = Line.get_rows(self.database_config.get('lines'), obs=Line.lines(node=node))
            items += [(line['ID'], '%s [%s]' % (get_line(line['NODE-1'], line['NODE-2']), get_line_id(line['NDIV-1'], line['NDIV-2']))) 
                for line in lines]
        elif g.system_config.UseRefLineUnits == 2:
            if node:
                args = { 'local_node' : node }
            is_hide_empty = g.system_config.HideEmptyNodes
            items += [(int(x.ksd), check_line(x.line)) for x in gen_lines(args)
                if not is_hide_empty or x.line is not None]
        else:
            lines = Line.lines(node=node)
            items += [(int(line.ksd), '%s [%s]' % (get_line_fullname(line), get_line_id(line.kuo, line.kuov))) 
                for line in lines if get_line_name(line)]
        items = sorted(items, key=itemgetter(0))
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        if g.system_config.UseRefEmptyValue:
            items.insert(1, (-1, EMPTY_REFERENCE_VALUE,))
        return items

    #   --------
    #   HANDLERS
    #   --------

    def prepare(self):
        # DIVISIONS [tsch]
        self.divisions = self.get_items(Division, 'divisions')
        # NODES [tuo]
        self.nodes = self.get_items(Node, 'nodes')
        # LINES [tsd]
        self.lines = self.get_items(Line, 'lines')

        self.source_divisions = self.divisions[0]
        self.ordered_divisions = self.divisions[1]
        
        self.ordered_nodes = self.nodes[1]
        self.ordered_lines = self.lines[1]

        for line in self.ordered_lines:
            code = get_line_id(line.kuo or 0, line.kuov or 0)
            self.map_lines[code] = line

    def render(self, **kw):
        self.set_search()


class Base:

    def __init__(self, default_page, default_template, database_config, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('Base init')

        self.default_page = default_page
        self._template = default_template
        self._database_config = database_config

        self._view = self._database_config.get(self._template) or {}

        self._config = None

        super().__init__(*args, **kwargs)

        self.is_with_points = 0
        self.is_admin = current_user.is_administrator()
        self.today = _today()

        self._is_extra = 0

        self.root = ''
        self.query_string = ''
        self.base = ''

        self._args = {}

    def _init_state(self, engine, args, factory=None, **kwargs):
        if IsDeepDebug:
            print('Base initstate')

        self.engine = engine
        self._args = args or {}

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

    @property
    def is_error(self):
        return self.last_engine.is_error

    @staticmethod
    def set_factory(key, factory):
        if factory is not None and isinstance(factory, dict):
            x = factory.get(key)
            if x is not None and callable(x):
                return x
        return None

    def point(self, name):
        if not self.is_with_points:
            return

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> %s: %s sec' % (name, spent_time(self._started, self._finished)))

    def get_columns(self):
        return ' '.join(self.columns)
    
    def get_view_columns(self):
        columns = []
        with_class = self._view.get('with_class') or {}
        for name in self.columns:
            columns.append({
                'name'   : name,
                'header' : self._view['headers'].get(name)[0],
                'with_class' : with_class.get(name) and 1 or 0,
            })
        return columns

    def set_config(self, config):
        self._config = config

    def get_config(self):
        return self._config or self._database_config[self._template]


class ViewRender(Base):

    def __init__(self, page, template, database_config, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('ViewRender init')

        super().__init__(page, template, database_config, *args, **kwargs)

        self.is_with_points = 0

        self._page = 0
        self._per_page = 0
        self._with_chunks = 1
        self._chunk = default_chunk
        self._next_row = 0
        self._pages = 0
        self._top = 0
        self._offset = 0
        self._position = None
        self._line = 1
        self._np = 0

        self._iter_pages = None
        self._per_page_options = None
        self._page_options = {}
        self._is_state = 0
        self._current_filter = None
        self._current_file = None

        self.is_yesterday = 0
        self.is_tomorrow = 0
        self.is_today = 0
        self.is_today_filter = 0
        self._selected_date = None
        self._date_from = None
        self._date_to = None

        self._messages = []
        self._statuses = []

        self._users = []
        self._selected_user = None
        self._selected_status = None
        self._selected_state = None
        self._search = None

        self._command = ''
        self._modes = None
        self._current_sort = 0
        self._sorted_by = 0
        self._order = ''
        self._desc_orders = None
        self._state = None
        
        self.params = None

    def _init_state(self, engine, args, factory=None, **kwargs):
        if IsDeepDebug:
            print('ViewRender initstate')

        super()._init_state(engine, args, factory=factory, **kwargs)

        self._statuses = [
            (0, '---', DEFAULT_UNDEFINED),
            (1, 'ERROR', maketext('Log Software Errors')),
            (2, 'WARNING', maketext('Log Software Warnings')),
            (3, 'INFO', maketext('Log User Events Info')),
        ]

        self.rows = []
        self.selected_row = {}
        self.total_selected = 0
        self._total_rows = 0
        self.is_selected = False
        self.selected = 0

        self.loader = ''
        self.pagination = {}

        self.id_column = None
        self.name_column = None

        self.is_editable = True
        self.confirmed_log_id = 0
        self.log_id = 0

    @property
    def requested_dates(self):
        if not self.is_today_filter and self._selected_date == '*':
            return ('*')
        dates = []
        date = self._date_from
        while date:
            if date not in dates:
                dates.append(date)
            if not self._date_to or date == self._date_to:
                break
            date = _evaluate_date(date, 1)

        return dates
    @property
    def columns(self):
        return self._view.get('columns')
    @columns.setter
    def columns(self, value):
        self._view['columns'] = value
    @property
    def headers(self):
        return self._view.get('headers')
    @headers.setter
    def headers(self, value):
        self._view['headers'] = value
    @property
    def view(self):
        return self._view
    @property
    def args(self):
        return self._args
    @property
    def page(self):
        return self._page
    @property
    def per_page(self):
        return self._per_page
    @per_page.setter
    def per_page(self, value):
        self._per_page = value
    def with_chunks(self):
        return self._with_chunks
    @per_page.setter
    def with_chunks(self, chunk):
        self._with_chunks = chunk and 1 or 0
        self._chunk = chunk
    @property
    def pages(self):
        return self._pages
    @pages.setter
    def pages(self, value):
        self._pages = value
    @property
    def total_rows(self):
        return self._total_rows
    @property
    def line(self):
        return self._line
    @line.setter
    def line(self, value):
        self._line = value
    @property
    def top(self):
        return self._top
    @property
    def date_from(self):
        return self._date_from
    @property
    def date_to(self):
        return self._date_to
    @property
    def command(self):
        return self._command
    @property
    def offset(self):
        return self._offset or 0
    @property
    def iter_pages(self):
        return self._iter_pages
    @property
    def page_options(self):
        return self._page_options
    @property
    def per_page_options(self):
        return self._per_page_options
    @property
    def statuses(self):
        return self._statuses
    @property
    def current_file(self):
        return self._current_file
    @property
    def current_sort(self):
        return self._current_sort
    @property
    def selected_status(self):
        return self._selected_status
    @property
    def messages(self):
        return self._messages
    @property
    def is_state(self):
        return self._is_state
    @property
    def order(self):
        return self._order
    @order.setter
    def order(self, value):
        self._order = value
    @property
    def desc_orders(self):
        return self._desc_orders or ()
    @desc_orders.setter
    def desc_orders(self, values):
        self._desc_orders = values
    @property
    def status(self):
        return self._selected_status is not None and self._selected_status[0] > 0 and self._selected_status[1] or ''
    @property
    def state(self):
        return self._state or ''
    @property
    def search(self):
        return self._search or ''
    @property
    def selected_user(self):
        return self._selected_user
    @property
    def user(self):
        return self._selected_user and self._selected_user[0] and self._selected_user[1] or ''
    @property
    def users(self):
        return self._users
    @property
    def has_filter(self):
        return (self.selected_status[0] or self._selected_user or self._search) and 1 or 0
    @property
    def filter(self):
        items = (
            self.status,
            self.user,
            self.search,
        )
        return ':'.join([x for x in items if x])
    @property
    def selected_date(self):
        return self._selected_date
    @selected_date.setter
    def selected_date(self, value):
        self._selected_date = value
    @property
    def selected_row(self):
        return self._selected_row
    @selected_row.setter
    def selected_row(self, value):
        self._selected_row = value
        self.is_selected = True

    def set_users(self):
        self._users = list(get_users_dict(as_dict=True).keys())
        self._users.insert(0, DEFAULT_UNDEFINED)
        user = self._args.get('user')
        self._selected_user = user and user[1] not in (DEFAULT_UNDEFINED, '', None) and user or ''

    def set_statuses(self, statuses):
        self.statuses = statuses

    def set_selected_status(self):
        status = self._args.get('status')
        self._selected_status = status and (status[1], self._statuses[status[1]][1], 'STATUS')

    def set_search(self):
        # ------------------------
        # Поиск контекста (search)
        # ------------------------
        self._search = get_request_search() or None

    def get_search(self):
        return self._search and ("&search=%s" % self._search) or self._search or ''

    def set_filter_by_dates(self):
        # ----------------------
        # Фильтр по датам (args)
        # ----------------------
        
        self.is_yesterday = self.is_tomorrow = self.is_today = False
        
        selected_date = self._args.get('selected_date')
        self._selected_date = selected_date and selected_date[1] or None

        date_from = self._args.get('date_from')
        date_to = self._args.get('date_to')
        
        self._date_from = date_from and date_from[1] or self._selected_date or self.today
        self._date_to = date_to and date_to[1] or None
        
        self.is_today_filter = False

    def set_filter_by_current_date(self):
        # -------------------
        # Фильтр текущего дня
        # -------------------

        if self._args:
            is_yesterday = self._args.get('is_yesterday')
            is_tomorrow = self._args.get('is_tomorrow')
            is_today = self._args.get('is_today')

            self.is_yesterday = is_yesterday and is_yesterday[1] or 0
            self.is_tomorrow = is_tomorrow and is_tomorrow[1] or 0
            self.is_today = is_today and is_today[1] or self._date_from == self.today and 1 or 0

            self.is_today_filter = self.is_yesterday or self.is_tomorrow or self.is_today

            if self.is_today_filter:
                if self.is_yesterday:
                    self._args['date_from'][1] = self._args['date_to'][1] = self._date_from = _evaluate_date(self._date_from, -1)
                if self.is_tomorrow:
                    self._args['date_from'][1] = self._args['date_to'][1] = self._date_from = _evaluate_date(self._date_from, 1)

                today = self._args.get('today')

                self.is_today = today and today[1] or (self._date_from == self.today and not self.is_yesterday) and 1 or 0

                if self.is_today:
                    self._date_from = self.today
                    self._args['date_from'] = ['TIMESTAMP', self._date_from]
                    self._args['date_to'] = ['TIMESTAMP', None]

                if not (self.is_yesterday or self.is_tomorrow or self.is_today) and self.is_today_filter:
                    self._date_from = None
                else:
                    self._selected_date = ''

    def set_command(self, **kw):
        # -----------------------------------
        # Команда панели управления (сommand)
        # -----------------------------------
        self._command = kw.get('command') or get_request_item('command')

    def set_order(self):
        # ---------------------------------
        # Сортировка журнала (current_sort)
        # ---------------------------------
        self._current_sort = int(get_request_item('sort') or '0')
        if self._current_sort > 0 and self._current_sort < len(self.view['columns']):
            self._order = '%s' % self.view['columns'][self._current_sort]
        else:
            self._order = 'ID'

        if self._current_sort in self.desc_orders:
            self._order += " desc"

    def set_state(self):
        # ----------------------
        # Условие отбора (state)
        # ----------------------
        state = get_request_item('state')
        self._is_state = state and state != 'R0' and True or False

        self._args.update({
            'state' : ('State', state)
        })

    def set_current_filter(self, value):
        self._current_filter = value

    def set_current_file(self, value):
        self._current_file = value

    def get_current_sort(self):
        return (isinstance(self._current_sort, int) or self._current_sort.isdigit()) and \
            ("&sort=%s" % self.current_sort) or self._current_sort

    def get_date_from(self):
        return self._date_from and ("&date_from=%s" % self.date_from) or self._date_from or ''

    def get_date_to(self):
        return self._date_to and ("&date_to=%s" % self.date_to) or self._date_to or ''

    def get_selected_status(self):
        return self._selected_status and ("&status=%s" % self.status) or self._selected_status or ''

    def get_selected_user(self):
        return self._selected_user and ("&user=%s" % self.selected_user) or self._selected_user or ''

    def get_state(self):
        return self.state and ("&state=%s" % self.state) or self._selected_state or ''

    def get_current_filter(self):
        return self._current_filter or ''

    def set_page_params(self):
        # -----------------------------------
        # Параметры страницы (page, per_page)
        # -----------------------------------
        self._page, self._per_page = get_page_params(self.default_page)
        self._top, self._offset = _get_top(self._per_page, self._page)

        self._page_options = {
            'page'     : self._page,
            'per_page' : self._per_page,
            'top'      : self._top, 
            'offset'   : self._offset
        }

    def set_position(self):
        # --------------------------------------------
        # Позиционирование строки в журнале (position)
        # --------------------------------------------
        self._position = get_request_item('position').split(':')
        self._line = self._line == 0 and len(self._position) > 3 and int(self._position[3]) or 1

        self._per_page_options = (5, 10, 20, 30, 40, 50, 100,)
        if self.is_admin:
            self._per_page_options += (250, 500)

    def set_page_iters(self):
        self._iter_pages = []
        for n in range(1, self._pages+1):
            if checkPaginationRange(n, self._page, self._pages):
                self._iter_pages.append(n)
            elif self._iter_pages[-1] != -1:
                self._iter_pages.append(-1)

        self.root = '%s/' % request.script_root
        self.query_string = 'per_page=%s' % self._per_page
        self.base = 'index?%s' % self.query_string

        self._is_extra = has_request_item(EXTRA_)

        columns = self.columns
        headers = self.headers

        if columns and headers and self._current_sort < len(columns):
            self._modes = [(n, '%s' % headers[x][0]) for n, x in enumerate(columns)]
            self._sorted_by = headers[columns[self._current_sort]]

    def rows_reset(self, with_page_params=None):
        self.rows = []
        #self._total_rows = 0
        self._np = 0
        self._selected_row = None
        self.is_selected = False

        if with_page_params:
            self._page = self._per_page = self._top = self._offset = 0

    def before(self, id_column, name_column, log_id, **kw):
        self.id_column = id_column or 'ID'
        self.name_column = name_column
        self.log_id = log_id

        self.rows_reset()

        if not self._total_rows and 'total_rows' in kw:
            self._total_rows = kw['total_rows']

        self.set_page_params()

    def render(self, **kw):
        # ----------------------
        # Условия отбора записей
        # ----------------------
        self.set_users()
        self.set_selected_status()
        self.set_search()
        self.set_position()
        self.set_filter_by_dates()
        self.set_filter_by_current_date()
        self.set_command(**kw)
        self.set_order()
        self.set_state()

    def row_iter(self, row, **kw):
        self.confirmed_log_id = 0

        np = self._np or self._offset or 0

        self.is_editable = isinstance(row, dict)

        np += 1

        if self._with_chunks and self._total_rows > self._chunk and np > self._chunk:
            return 1

        if row is not None and self.is_editable:
            if not self.is_selected and self.log_id:
                if not self.confirmed_log_id and self.log_id == row.get(self.id_column):
                    self.confirmed_log_id = self.log_id
                if self.log_id == row.get(self.id_column):
                    row['selected'] = 'selected'
                    self._selected_row = (self.log_id, np+1, row)
                    self.is_selected = True
            else:
                row['selected'] = ''

            if not row.get('id'):
                row['id'] = row.get(self.id_column)
            if not row.get('pk'):
                row['pk'] = row.get('id')

            row['np'] = np

            if not self.is_selected and self._next_row > 0 and self._next_row == np:
                row['selected'] = 'selected'
                self.log_id = row.get(self.id_column)
                self._selected_row = (self.log_id, np, row)
                self.is_selected = True

        self.rows.append(row)

        self._np = np
        
        return 0

    def row_finish(self):
        if not self.rows:
            return

        if not self._total_rows:
            self._total_rows = len(self.rows)

        if self.order:
            key = self.view['columns'][self.current_sort]
            reverse = 'desc' in self._order
            self.rows = sorted(self.rows, key=itemgetter(key), reverse=reverse)

        if self._line > len(self.rows) or self._line < 0:
            self._line = self._total_rows
        elif self._line == 0:
            self._line = 1

        if not self.is_selected and len(self.rows) >= self._line:
            row = self.rows[self._line-1]
            if self.is_editable:
                self.confirmed_log_id = self.log_id = row.get('id')
                row['selected'] = 'selected'
            self._selected_row = (self.log_id, self._line-1 or 1, row)
            self.is_selected = True

        if self._per_page > 0:
            self._pages = math.ceil(self._total_rows / self._per_page)
        else:
            self._pages = 1
            self._per_page = self._total_rows

        if not self._page or self._page > self._pages:
            self._page = 1

    def after(self):
        # --------------------------------------
        # Нумерация страниц журнала (pagination)
        # --------------------------------------
        per_page = self._per_page
        page = self._page
        next_row = 0

        if self._with_chunks and self._total_rows > self._chunk:
            if self.params:
                next_chunk = self.params.get('next_chunk')
                chunk = self.params.get('chunk')
                next_row = self.params.get('next_row')
                number = self.params.get('number')
                per_page = self._chunk
                page = math.ceil(next_chunk[1] / per_page)
            else:
                next_chunk = [0, 0]
                per_page = self._chunk  
                page = 1

        self._top, self._offset = _get_top(per_page, page)
        self._line = next_row 

        offset = self._offset
        top = min(self._top, self._total_rows)

        if self._total_rows > per_page and len(self.rows) > top:
            self.rows = self.rows[offset : top]

        total_rows = len(self.rows)

        if next_row and total_rows:
            row = self.rows[next_row - next_chunk[0]]
            row['selected'] = 'selected'
            self.log_id = '%s_%s' % (row.get('id'), self._line)
            self._selected_row = (self.log_id, self._line or 1, row)

        self.set_page_iters()

    @property
    def default_link(self):
        return '%s%s%s%s' % (
                self.base, 
                self.get_current_filter(),
                self.get_search() or '',
                self.get_current_sort() or '',
                )

    def set_pagination(self, action, link):
        self.pagination = {
            'total'             : '%s' % (self.total_rows),
            'total_selected'    : '%s | 0.00' % (self.total_selected or 0),
            'per_page'          : self.per_page,
            'pages'             : self.pages,
            'current_page'      : self.page,
            'selected'          : self.is_selected and self.selected_row or (0, 0, None),
            'iter_pages'        : tuple(self.iter_pages),
            'with_chunks'       : [self._with_chunks, self._chunk],
            'has_next'          : self.page < self.pages,
            'has_prev'          : self.page > 1,
            'per_page_options'  : self.per_page_options,
            'action'            : action or '',
            'link'              : link,
            'sort'              : {
                'modes'         : self._modes,
                'sorted_by'     : self._sorted_by,
                'current_sort'  : self._current_sort,
            },
            'position'          : '%d:%d:%d:%d' % (self.page, self.pages, self.per_page, self.line),
            'today'             : {
                'selected'      : self.is_today,
                'date_from'     : self._date_from,
                'has_prev'      : self.is_today or self.is_yesterday,
                'has_next'      : self._date_from and self._date_from < self.today and True or False,
            },
        }

    def response(self, **kw):
        title = kw.get('title') or 'Application %s Page' % Capitalize(self.default_page)
        data_title = kw.get('data_title') or ''
        self.loader = kw.get('loader') or url_for('%s.loader' % self.default_page)
        link = kw.get('link') or self.default_link or ''
        action = kw.get('action') or ''

        self.set_pagination(action, link)

        if self._is_extra:
            self.pagination['extra'] = 1
            self.loader += '?%s' % EXTRA_

        return {
            'base'              : self.base,
            'page_title'        : maketext(title),
            'data_title'        : data_title,
            'header_subclass'   : 'left-header',
            'show_flash'        : True,
            'is_full_container' : 1,
            'is_no_line_open'   : 0, 
            'model'             : 0,
            'loader'            : self.loader,
            'pagination'        : self.pagination,
            'semaphore'         : initDefaultSemaphore(),
            'args'              : self.args,
            'current_file'      : self.current_file,
            'selected_date'     : self.selected_date,
            'messages'          : self.messages,
            'tabs'              : _check_extra_tabs(self.selected_row).keys(),
            'navigation'        : get_navigation(),
            'group'             : self._template,
            'config'            : self.get_config(),
            'columns'           : self.get_view_columns(),
            'rows'              : self.rows,
            'total_rows'        : self.total_rows,
            'search'            : self.search or '',
        }


class View:

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('View init')

        self.page = page

        self.database_config = database_config

        self.name = ''
        self.template = ''

        self.title = ''
        self.data_title = ''
        self.link = ''

        self._view = None
        self._response = {}
        self._args = {}
        self._total_rows = 0

        self.handler = None
        self.is_gen = 0

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('View initstate')

        self.engine = engine

        self._args = args

        self.config = self.template and self.database_config.get(self.template) or {}

        self._view = ViewRender(self.page, self.template, self.database_config)
        self._view._init_state(engine, args)

        self.page_title = 'Application %s Page' % Capitalize(self.page)
        self.data_title = ''

        self.is_gen = kw.get('is_gen') and 1 or 0
        self._view.with_chunks = kw.get('with_chunks') or 0

        self.action = kw.get('action') or url_for('%s.start' % self.page)

    @property
    def args(self):
        return self._args or {}
    @property
    def view(self):
        return self._view
    @property
    def search(self):
        return self._view._search
    @property
    def page_options(self):
        return self._view._page_options
    @property
    def total_rows(self):
        return self._total_rows
    @property
    def response(self):
        return self._response

    def begin(self, id_column, name_column, log_id, params=None, **kw):
        if not log_id or 'id' in kw:
            log_id = int(kw.get('id') or 0)

        self._view.render(**kw)

        self._view.params = params
        self._next_row = params and int(params.get('next_row', 0)) or 0
        self._view.before(id_column, name_column, log_id, **kw)

        if not self._total_rows:
            self._view.per_page = kw.get('per_page') or 0

    def finish(self, page_title, data_title, action, link, **kw):
        self._view.after()
        
        self.data_title = maketext(data_title)
    
        self._response = self._view.response(
            title=maketext('%s Page' % page_title),
            data_title=self.data_title, 
            action=action,
            link=link,
            )

    def set_total_rows(self, cls, **kw):
        self._total_rows = cls.ordered_rows(is_query=True, **kw).count()
        self._view._total_rows = self._total_rows

    def set_current_filter(self, value):
        self._view.set_current_filter(value)

    def next_pk(self, mode):
        if self.engine is not None:
            if mode == 'messagetype':
                ob = MessageType()
                return ob.next_pk()

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        pass

    @staticmethod
    def get_original_column(c):
        column = None
        if c.startswith('rel'):
            x = c.split(':')
            column = x[2]
        elif c.startswith('date'):
            x = c.split(':')
            column = x[1]
        else:
            column = c
        return column

    def register_errors(self, module, errors):
        if not errors:
            return
        for error in errors:
            g.app_logger(module or '%s.%s' % (self.page, self.__class__.__name__), error, is_error=True)

    def register_data(self, pk, command, **kw):
        return self.handler(pk, command, **kw)

    @staticmethod
    def check_sql_value(value):
        return value and isinstance(value, str) and not value.isdigit() and getSQLString(value) or sint(value, with_zero=True)

    def is_key_valid(self, key, value, errors):
        is_error = False

        header = self.config['headers'].get(key)[0]

        k = key.lower() 

        if 'port' in k:
            if not (isinstance(value, str) and len(value) == 5):
                errors.append('%s: %s[%s]' % (
                        g.maketext("Port number is incorrect (XXXX)"), 
                        header, 
                        value,
                    ))
                is_error = True
            elif not value.isdigit():
                errors.append('%s: %s[%s]' % (
                        g.maketext("Port value is not a number"), 
                        header, 
                        value,
                    ))
                is_error = True
            else:
                n = int(value)
                if not (n > 51999 and n < 56001):
                    errors.append('%s: %s[%s]' % (
                            g.maketext("Port value is not in a valid range (52000-56000)"), 
                            header, 
                            value,
                        ))
                    is_error = True

        elif k == 'ip':
            if not (isinstance(value, str) and len(value) < 15 and '.' in value):
                errors.append('%s: %s[%s]' % (
                        g.maketext("IP-address is incorrect (XXX.XXX.XXX.XXX)"), 
                        header, 
                        value,
                    ))
                is_error = True

            parts = value.split('.')

            if len(parts) != 4:
                errors.append('%s: %s[%s]' % (
                        g.maketext("IP-address is incorrect (not 4 parts)"), 
                        header, 
                        value,
                    ))
                is_error = True

            if not is_error:
                for index, x in enumerate(parts):
                    if not x.isdigit():
                        errors.append('%s: %s[%s]' % (
                                g.maketext("IP-address is incorrect (not a number)"), 
                                header, 
                                x,
                            ))
                        is_error = True
                        break
                    n = int(x)
                    if n > 255 or (n == 1 and index == 0) or n < 0:
                        errors.append('%s: %s[%s] (%s)' % (
                                g.maketext("IP-adress is not in valid range"), 
                                header,
                                x,
                                index == 0 and '1-255' or '0-255',
                            ))
                        is_error = True
                        break

        return is_error

    def check_values(self, command, params, errors, kw):
        is_error = None

        if self._view is not None:
            export = self.config.get('export')
            original = self.config.get('original')
            for n, key in enumerate(export):
                k = key.lower()
                column = self.get_original_column(original[n])
                if k in params and k not in 'id:pk' and column:
                    value = params[k]
                    is_error = self.is_key_valid(key, value, errors)
                    if not is_error:
                        kw[column] = self.check_sql_value(value)
                    else:
                        break
        else:
            is_error = True
            errors.append(g.maketext('Unexpected error!'))

        return is_error

    def save(self, command, params):
        errors, kw = [], {}
        is_error = self.check_values(command, params, errors, kw)

        if not is_error:
            pk = int(params.get('pk') or params.get('id') or 0)
            is_error, errors = self.register_data(pk, command, **kw)

        if is_error:
            self.register_errors(None, errors)

        return is_error or False, errors

    def check_string_key_is_exist(self, key, value, **kw):
        is_error = 0

        def _get(v):
            return ''.join([x.strip().lower() for x in v.split(' ')])

        pk = int(kw.get('pk'))

        v = _get(value)

        k = key.upper()

        for row in self.view.rows:
            x = int(row.get('pk') or 0)
            if _get(row.get(k)) == v and (not pk or x != pk):
                is_error = 1
                break

        return is_error

    def check_numeric_key_is_exist(self, key, value, **kw):
        is_error = 0

        def _get(v):
            return isinstance(v, str) and v.isdigit() and sint(v, with_zero=1) or v

        pk = int(kw.get('pk'))

        v = _get(value)

        k = key.upper()

        for row in self.view.rows:
            x = int(row.get('pk') or 0)
            if _get(row.get(k)) == v and (not pk or x != pk):
                is_error = 1
                break

        return is_error

    def check_range_key_is_exist(self, key, value, **kw):
        """
            Special for Ports range check:
            key -- names: (key1, key2)
            value -- values range of integer: (value1, value2)
            title -- param custom title
        """
        is_error = 0

        def _get(v0, v1):
            try:
                return v0 and v1 and v1 >= v0 and set(range(int(v0), int(v1)+1)) or None
            except:
                print_to(None, '_get.raise:%s-%s' % (v0, v1))
                return None

        pk = int(kw.get('pk'))

        vrange = _get(value[0], value[1])

        #print_to(None, 'vrange: %s' % vrange)

        k0 = key[0].upper()
        k1 = key[1].upper()

        values = []
        for n, row in enumerate(self.view.rows):
            rpk = int(row.get('pk') or 0)
            state = int(row.get('state'))
            if (not pk or rpk != pk) and state > 0:
                v = (_get(row.get(k0), row.get(k1)), rpk)
                if v:
                    #print_to(None, 'pk:%s-%s : v:%s' % (pk, rpk, v))
                    values.append(v)

        matched = []
        pks = []
        for value, rpk in values:
            if value:
                x = list(value.intersection(vrange))
                if x and len(x) > 0:
                    if len(x) == 1:
                        x.append(x[0])
                    if not x in matched:
                        matched.append(x)
                        pks.append(rpk)

        matched = dict(zip(pks, matched))

        if matched:
            is_error = 1

        #print_to(None, 'matched: %s' % matched)

        values = None

        return is_error, matched

    def check_if_exist(self, keys, params):
        is_error = False
        errors = []

        pk = params.get('id')

        for key, ctype, title in keys:
            if isIterable(key):
                value = (params.get(key[0]), params.get(key[1]))
            else:
                value = params.get(key)
            if not value or isIterable(value) and len(list(filter(None, value))) == 0:
                continue
            if ctype == 'str' and self.check_string_key_is_exist(key, value, pk=pk):
                is_error = True
                errors.append('%s: %s' % (g.maketext('%s with given %s already exists' % (Capitalize(self.name), title)), value))
                break
            elif ctype == 'num' and self.check_numeric_key_is_exist(key, value, pk=pk):
                is_error = True
                errors.append('%s: %s' % (g.maketext('%s with given %s already exists' % (Capitalize(self.name), title)), value))
                break
            elif ctype == 'range':
                is_error, matched = self.check_range_key_is_exist(key, value, pk=pk)
                if is_error:
                    values = ', '.join(['%s-%s[ID:%s]' % (x[0], x[-1], pk) for pk, x in matched.items() if x and len(x) >= 2])
                    errors.append('%s: %s' % (g.maketext('%s with given %s already used' % (Capitalize(self.name), title)), values))
                break

        return is_error, errors


class Divisions(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('Divisions init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = 'division'
        self.template = 'divisions'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('Divisions initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'NAME'
        sort_type = ''

        log_id = int(kw.get('division_id') or 0)

        params = kwargs.get('params')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================

        if self.engine is not None:
            
            rows = Division.get_rows(self.config)

            for row in rows:
                if self._view.row_iter(row):
                    break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

    def next_pk(self):
        return None

    def save(self, command, params):
        self.handler = registerDivision
        is_error, errors = super().save(command, params)

        return is_error or False, errors


class Nodes(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('Nodes init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = 'node'
        self.template = 'nodes'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('Nodes initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'NAME'
        sort_type = ''

        log_id = int(kw.get('node_id') or 0)

        params = kwargs.get('params')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================

        if self.engine is not None:
            
            rows = Node.get_rows(self.config)

            for row in rows:
                row['state'] = row['STATE']
                row['STATE'] = row['state'] and 'Да' or 'Нет'
                if row['state']:
                    row['Ready'] = 1
                elif not row['state']:
                    row['Error'] = 1
                if self._view.row_iter(row):
                    break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

        kw[self.name]['states'] = [(0, 'Нет'), (2, 'Да'),]

    def next_pk(self):
        if self.engine is not None:
            ob = Node()
            return ob.next_pk()

    def save(self, command, params):
        self.handler = registerNode
        key = 'state'
        state = params.get(key)
        pk = params.get('id')
        if not g.system_config.UpdateParamsForInActive:
            if not state:
                params = {key: 0, 'pk': pk}
            else:
                params[key] = 2
        else:
            params[key] = state and 2 or 0
        if not g.system_config.UpdateIpPortsForNodeTop:
            key = 'ndiv'
            if key in params:
                ndiv = int(params.get(key) or 0)
                if ndiv == 0 and state:
                    del params['ip']
                    del params['port1']
                    del params['port2']

        is_error, errors = False, None

        if state:
            keys = (('ip', 'str', 'ip-address'), (('port1', 'port2'), 'range', 'port range'),)
            is_error, errors = self.check_if_exist(keys, params)

        if not is_error:
            is_error, errors = super().save(command, params)

        return is_error or False, errors


class MessageTypes(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('MessageTypes init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = 'messagetype'
        self.template = 'messagetypes'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('MessageTypes initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'NAME'
        sort_type = ''

        log_id = int(kw.get('messagetype_id') or 0)

        params = kwargs.get('params')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================
    
        if self.engine is not None:
            
            rows = MessageType.get_rows(self.config)
            
            for row in rows:
                if self._view.row_iter(row):
                    break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

        kw[self.name]['priorities'] = [(n) for n in range(0, 10)]

    def next_pk(self):
        if self.engine is not None:
            ob = MessageType()
            return ob.next_pk()

    def save(self, command, params):
        self.handler = registerMessageType

        keys = (('name', 'str', 'name'),)
        is_error, errors = self.check_if_exist(keys, params)

        if not is_error:
            is_error, errors = super().save(command, params)

        return is_error or False, errors


class Binds(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('Binds init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = 'bind'
        self.template = 'binds'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('Binds initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'DIVISION'
        name_column = 'STATE'
        sort_type = ''

        log_id = int(kw.get('bind_id') or 0)

        params = kwargs.get('params')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================
    
        if self.engine is not None:
            
            rows = Bind.get_rows(self.config)
            
            for row in rows:
                if self._view.row_iter(row):
                    break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

    def next_pk(self):
        if self.engine is not None:
            ob = Bind()
            return ob.next_pk()

    def save(self, command, params):
        self.handler = registerBind
        is_error, errors = super().save(command, params)

        return is_error or False, errors


class Lines(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('Lines init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = 'line'
        self.template = 'lines'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('Lines initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'NODE'
        sort_type = ''

        log_id = int(kw.get('line_id') or 0)

        params = kwargs.get('params')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================
    
        if self.engine is not None:
            
            rows = Line.get_rows(self.config)
            
            for row in rows:
                if self._view.row_iter(row):
                    break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

    def next_pk(self):
        if self.engine is not None:
            ob = Line()
            return ob.next_pk()

    def save(self, command, params):
        self.handler = registerLine
        is_error, errors = super().save(command, params)

        return is_error or False, errors


class LineStates(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('LineStates init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = kwargs.get('name') or 'linestate'
        self.template = kwargs.get('template') or 'linestates'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('LineStates initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'LINE'
        sort_type = ''

        if self.template == 'activities':
            id_column = 'CODE'

        log_id = int(kw.get('linestate_id') or 0)

        params = kwargs.get('params')
        args = self.args

        #if self.name in ('activities', 'reliabilities'):
        #    self.set_total_rows(LineState, args=args, mode='linestates')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        # ==========================
        # >>> Выборка данных журнала
        # ==========================

        if self.engine is not None:
            
            if self.template == 'linestates':
                if self.is_gen:
                    for row in LineState.gen_rows(self.config, args=args, mode='linestates'):
                        if self._view.row_iter(row):
                            break
                else:
                    #rows = LineState.get_rows(self.config, obs=LineState.states(), as_is=True)
                    #rows = LineState.get_rows(self.config, as_is=True)
    
                    for row in LineState.ordered_rows():
                        if self._view.row_iter(row):
                            break
            else:
                row_iter = kwargs.get('row_iter')
                cls = kwargs.get('cls')

                self._view.rows_reset(with_page_params=True)

                if self.template == 'activities':
                    for row in gen_activities(args):
                        if row_iter is not None:
                            row = row_iter(cls, row, args)
                        if row is None and g.system_config.HideEmptyNodes:
                            continue

                        if self._view.row_iter(row):
                            break

                if self.template == 'reliabilities':
                    rows = {}
                    for row in gen_reliabilities(args):
                        row_iter(cls, row, rows, args)

                    period, begin, end = kwargs.get('period')

                    for row in rows.values():
                        off = row['OFF']
                        on = row['ON']
                        is_off = row['is_off']
                        is_on = row['is_on']
                        value = (((on-(is_on and begin or 0))/(period or 1)) * 100)
                        row['VALUE'] = '%s%%' % round(value, 2)
                        if 100 - value < 10:
                            row['Ready'] = True
                        elif value < 10:
                            row['Error'] = True

                        if self._view.row_iter(row):
                            break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

    def save(self, command, params):
        self.handler = registerLineState
        is_error, errors = super().save(command, params)

        return is_error or False, errors


class Messages(View):

    def __init__(self, page, database_config, *args, **kwargs):
        if IsDeepDebug:
            print('Messages init')

        super().__init__(page, database_config, *args, **kwargs)

        self.name = kwargs.get('name') or 'message'
        self.template = kwargs.get('template') or 'messages'

    def _init_state(self, engine, args=None, factory=None, **kw):
        if IsDeepDebug:
            print('Messages initstate')

        super()._init_state(engine, args=args, factory=factory, **kw)

    def _check_center_error(self,row):
        r1 = row.get('r1')
        r2 = row.get('r2')
        if r1 == 1 and r2 == 1:
            row['Ready'] = True
        if r1 in (0, 1):
            row['Err1'] = r1 == 0 and 'Да' or r1 == 1 and 'Нет' 
            row['Error'] = True
        else:
            row['Err1'] = ''
        if r2 in (0, 1):
            row['Err2'] = r2 == 0 and 'Да' or r2 == 1 and 'Нет' 
            row['Error'] = True
        else:
            row['Err2'] = ''

    @staticmethod
    def set_speed_type(values):
        keys = ('ID', 'LINE', 'VOLUME', 'TIME', 'VALUE', 'TOTAL', 'ERRORS', 'order')
        x = dict([(key, values[n]) for n, key in enumerate(keys)])
        x.update({
            'speed'  : 0,
            'volume' : 0,
            'time'   : 0,
            'errors' : 0,
        })
        return x

    @staticmethod
    def set_speed(row, speed, volume, time, errors, is_total):
        row['speed'] += speed
        row['volume'] += volume
        row['time'] += time
        row['errors'] += errors
        row['VOLUME'] = round(row['volume'] / 1024, 2)
        row['TIME'] = round(row['time'] / 60, 2)
        
        if is_total:
            sp = row['volume'] / row['time'] / 60
        else:
            sp = row['speed']

        row['VALUE'] = sp and ('%s' % round(sp, 2)) or '0.00'
        row['ERRORS'] = row['errors'] or 0

    @staticmethod
    def set_capacity_messagetype(values):
        keys = ('ID', 'LINE', 'TOTAL', 'VOLUME', 'order')
        return dict([(key, values[n]) for n, key in enumerate(keys)])

    @staticmethod
    def set_messagetype_column(messagetype):
        return { 'MESSAGETYPE': messagetype, 'capacity': [0, 0], 'volume': 0, 'VALUE': '' }

    @staticmethod
    def set_capacity(column, capacity, volume, is_total): 
        c0 = (column['capacity'][0]) + capacity[0]
        c1 = (column['capacity'][1]) + capacity[1]
        column['capacity'] = [c0, c1]
        column['volume'] += sum(volume)
        column['VALUE'] = volume and ('%s-%s [%s]' % (c0, c1, str(column['volume']))) or ''

    def make(self, page_title, data_title, action, link, kw, **kwargs):
        self._view.set_current_file({
            'id'       : self.name, 
            'name'     : self.name,
            'disabled' : '',
            'value'    : '',
        })

        id_column = 'ID'
        name_column = 'NUMBER'
        sort_type = ''

        log_id = int(kw.get('message_id') or 0)
        
        params = kwargs.get('params')
        args = self.args

        if self.name in ('messages', 'center'):
            self.set_total_rows(Message, args=args, mode='messages')

        self.begin(id_column, name_column, log_id, params=params, **kw)

        page_options = self.page_options

        # ==========================
        # >>> Выборка данных журнала
        # ==========================

        if self.engine is not None:

            if self.template == 'messages':
                if self.is_gen and not self.search:
                    for row in Message.gen_rows(self.config, page_options=page_options, args=args, mode='messages'):
                        if self._view.row_iter(row):
                            break
                        self._check_center_error(row)

                else:
                    rows = Message.get_rows(self.config, page_options=page_options, args=args, mode='messages')
    
                    for row in rows:
                        if self._view.row_iter(row):
                            break
                        self._check_center_error(row)

            elif self.name == 'messages' and self.template == 'center':
                if self.is_gen:
                    for row in Message.gen_rows(self.config, args=args, query=Message.messages(is_query=True), page_options=page_options):
                        if self._view.row_iter(row):
                            break
                        self._check_center_error(row)
                else:
                    for row in Message.get_rows(self.config, args=args, query=Message.messages()):
                        if self._view.row_iter(row):
                            break
                        self._check_center_error(row)

            elif self.name == 'center' and self.template == 'center':
                row_iter = kwargs.get('row_iter')
                cls = kwargs.get('cls')

                for row in gen_center_exchange(args, page_options=page_options):
                    if row_iter is not None:
                        row = row_iter(cls, row, args)
                    if row is None and g.system_config.HideEmptyNodes:
                        continue
                    self._check_center_error(row)
                    if self._view.row_iter(row):
                        break

            elif self.template == 'capacities':
                row_iter = kwargs.get('row_iter')
                cls = kwargs.get('cls')

                vrows = {}
                for row in gen_capacities(args, page_options=page_options):
                    if row_iter is not None:
                        row = row_iter(cls, row, vrows, args)
                    if row is None and g.system_config.HideEmptyNodes:
                        continue

                grows = {}

                default_columns = 'ID:LINE:TOTAL:VOLUME:order:total:css'
                columns = []
                headers = {
                    'np'     : ('№ п/п', 'nowrap'),
                    'ID'     : ('ID', 'nowrap'),
                    'LINE'   : ('Направление', 'nowrap'),
                    'TOTAL'  : ('Всего сообщений', ''),
                    'VOLUME' : ('Объем данных [байт]', 'nowrap'),
                }

                gids = []

                for gid in vrows:
                    vrow = vrows[gid]
                    line = vrow['LINE']
                    total = vrow['TOTAL']
                    volume = vrow['VOLUME']
                    if gid not in grows:
                        grows[gid] = self.set_capacity_messagetype((gid, line, total, 0, gid))
                        gids.append(gid)

                    grow = grows[gid]

                    for key in vrow.keys():
                        if key not in default_columns:
                            item = vrow[key]
                            value = item['VALUE']
                            header = item['MESSAGETYPE']
                            if key not in grow:
                                grow[key] = value
                                if key not in columns:
                                    columns.append(key)
                            if key not in headers:
                                headers[key] = (header, 'nowrap')
                        else:
                            grow[key] = vrow[key]

                    grow['VOLUME'] += volume

                for key in grows:
                    for column in columns:
                        if column not in grows[key]:
                            grows[key][column] = ''

                rows = sorted([grows[gid] for gid in gids], key=itemgetter('order'))

                self._view.rows_reset(with_page_params=True)

                for row in rows:
                    if self._view.row_iter(row):
                        break

                columns = 'np:LINE'.split(':') + columns + 'TOTAL:VOLUME'.split(':')
                config = {
                    'columns' : columns,
                    'headers' : headers,
                    'view' : None,
                    'with_class' : { 'LINE' : True, 'VOLUME' : True },
                }

                self._view.columns = columns
                self._view.headers = headers

                self._view.set_config(config)

            elif self.template == 'speeds':
                row_iter = kwargs.get('row_iter')
                cls = kwargs.get('cls')

                vrows = {}
                for row in gen_speeds(args):
                    if row_iter is not None:
                        row = row_iter(cls, row, vrows, args)
                    if row is None and g.system_config.HideEmptyNodes:
                        continue

                rows = sorted(vrows.values(), key=itemgetter('order'))

                self._view.rows_reset(with_page_params=True)

                for row in rows:
                    if self._view.row_iter(row):
                        break

            self._view.row_finish()

        self.finish(page_title or self.page_title, data_title or self.data_title, action or self.action, link, **kw)

        kw[self.name] = self.response

    def save(self, command, params):
        self.handler = registerMessage
        is_error, errors = super().save(command, params)

        return is_error or False, errors

