# -*- coding: utf-8 -*-

from operator import itemgetter

from ..settings import *
from ..models import (
     Division, Node, MessageType, Bind, Line, LineState, gen_local_lines, get_activity_dates, get_messages_dates,
     get_users_dict
     )
from ..pages import (
     clean, check_int, check_line, get_line, get_item_code, 
     get_line_id, get_line_name, get_line_fullname,
     PageLocal
     )
from ..utils import (
     getDate, getToday, checkPaginationRange
     )

from app.semaphore.views import initDefaultSemaphore

##  ===============================
##  Page request parsing Main Class
##  ===============================

default_date_format = DEFAULT_DATE_FORMAT[1]

## ==================================================== ##

def _today():
    return getDate(getToday(), default_date_format)

def _get_page_args(query=None):
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    def _get_item(name, check_int=None):
        return get_request_item(name, check_int=check_int, args=query)

    try:
        args.update({
            'stock'       : ['StockListID', int(_get_item('stock') or '0')],
            'id'          : ['TID', _get_item('_id', check_int=True)],
            'ids'         : ['TID', get_request_item('_ids')],
        })
    except:
        args.update({
            'stock'       : ['StockListID', 0],
            'id'          : ['TID', None],
            'ids'         : ['TID', None],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##

class PageRender(PageLocal):

    def __init__(self, page, template, database_config, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('PageRender init')

        super().__init__(**kwargs)

        self.page = page
        self._template = template
        self._config = database_config

        self._view = self._config[self._template]

        self._users = []
        self._selected_user = None

        self._position = None
        self._line = 1
        self._iter_pages = None
        self._per_page_options = None

        self._current_filter = None
        self._command = ''
        self._current_sort = 0
        self._sorted_by = 0
        self._order = ''
        self._desc_orders = None
        self._search = None

        self.database_config = database_config

        self.is_with_points = 0
        self.is_admin = current_user.is_administrator()
        self.today = _today()

        self._is_extra = 0

        self.root = ''
        self.query_string = ''
        self.base = ''

        self._args = {}

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageRender initstate')

        super()._init_state(engine, args=args, factory=factory, **kwargs)

        self.engine = engine
        self._args = args
        self.factory = factory

    #   -----------

    @property
    def columns(self):
        return self._view['columns']
    @property
    def view(self):
        return self._view
    @property
    def args(self):
        return self._args or {}
    @property
    def page_link(self):
        return _PAGE_LINK
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
    def command(self):
        return self._command
    @property
    def current_sort(self):
        return self._current_sort

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

    def get_config(self):
        return self._config[self._template]

    #   --------------------
    #   PAGE DEFAULT FILTERS
    #   --------------------

    def set_command(self, **kw):
        # -----------------------------------
        # Команда панели управления (сommand)
        # -----------------------------------
        self._command = kw.get('command') or get_request_item('command')

    def set_current_filter(self, value):
        self._current_filter = value

    def set_order(self):
        # ---------------------------------
        # Сортировка журнала (current_sort)
        # ---------------------------------
        self._current_sort = int(get_request_item('sort') or '0')
        if self._current_sort > 0:
            self._order = '%s' % self.view['columns'][self._current_sort]
        else:
            self._order = 'ID'

        if self._current_sort in self.desc_orders:
            self._order += " desc"

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

        view = self._view

        self._modes = [(n, '%s' % view['headers'][x][0]) for n, x in enumerate(view['columns'])]
        self._sorted_by = view['headers'][view['columns'][self._current_sort]]

    def get_current_sort(self):
        return (isinstance(self._current_sort, int) or self._current_sort.isdigit()) and \
            ("&sort=%s" % self.current_sort) or self._current_sort

    def get_current_filter(self):
        return self._current_filter or ''

    def get_current_sort(self):
        return (isinstance(self._current_sort, int) or self._current_sort.isdigit()) and \
            ("&sort=%s" % self.current_sort) or self._current_sort

    #   ----------
    #   REFERENCES
    #   ----------

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
            items += [(int(x.ksd), x.line) for x in gen_local_lines(args)
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

    def ref_messages_dates(self):
        args = {}
        if self.local_node is not None:
            args = { 'local_node':self.local_node[0] }
        items = []
        items += [(x.date, x.date) for x in get_messages_dates(args)]
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        return items

    #   --------
    #   HANDLERS
    #   --------

    def render(self, **kw):
        super().render(**kw)

        self.set_search()
        self.set_position()
        self.set_command(**kw)
        self.set_order()

    def run(self, page_title=None, data_title=None, **kw):
        return kw

    def response(self, **kw):
        pass
