# -*- coding: utf-8 -*-

from operator import itemgetter

from ..settings import *
from ..models import (
     Division, Node, MessageType, Bind, Line, LineState, gen_lines, get_activity_dates, get_messages_dates,
     get_users_dict
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
    return clean(s.replace(':ЦУП-Е', ':КТС01'))

def get_line(node1, node2):
    return check_line('%s - %s' % (node1, node2))

def get_line_id(kuo, kuov):
    return clean('%s-%s' % (kuo, kuov))

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

class PageRender:

    def __init__(self, page, template, database_config, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('PageRender init')

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

        self.local_node = None
        self.selected_line = None
        self._args = {}

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageRender initstate')

        self.engine = engine
        self._args = args
        self.factory = factory

        if self.engine is None:
            pass
        
        self.get_local_node()

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
    def search(self):
        return self._search or ''
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
    def search(self):
        return self._search
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

    def set_search(self):
        # ------------------------
        # Поиск контекста (search)
        # ------------------------
        self._search = get_request_search() or None

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

    def get_search(self):
        return self._search and ("&search=%s" % self._search) or self._search or ''

    def get_current_filter(self):
        return self._current_filter or ''

    def get_current_sort(self):
        return (isinstance(self._current_sort, int) or self._current_sort.isdigit()) and \
            ("&sort=%s" % self.current_sort) or self._current_sort

    def render(self, **kw):
        self.set_search()
        self.set_position()
        self.set_command(**kw)
        self.set_order()

    def get_local_node(self):
        local_node = connection_params.local_node
        row = Node.get_local_node(local_node)
        if row is not None and row.kuo:
            self.local_node = (str(row.kuo), row.kikts, row.pikts)
        else:
            self.local_node = None

    def set_selected_line(self, line_id):
        if line_id is None:
            return
        _id = int(line_id)
        for line in self.ordered_lines:
            if line.ksd == _id:
                nodes = line.kuo or 0, line.kuov or 0
                code = get_line_id(nodes[0], nodes[1])
                name = get_line_name(line)
                self.selected_line = (line.ksd, name, nodes)
                break

    def set_selected_division(self, division_id):
        pass

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
        node = self.filter_items.get('local_node') and self.filter_items['local_node'][0] or None
        items = []
        if g.system_config.UseRefLineUnits == 1:
            lines = Line.get_rows(self.database_config.get('lines'), obs=Line.lines(node=node))
            items += [(line['ID'], '%s [%s]' % (get_line(line['NODE-1'], line['NODE-2']), get_line_id(line['NDIV-1'], line['NDIV-2']))) 
                for line in lines]
        elif g.system_config.UseRefLineUnits == 2:
            args = { 'selected_node' : node }
            items += [(int(x.ksd), check_line(x.line)) for x in gen_lines(args)]
        else:
            lines = Line.lines(node=node)
            items += [(int(line.ksd), '%s [%s]' % (get_line_fullname(line), get_line_id(line.kuo, line.kuov))) 
                for line in lines if get_line_name(line)]
        items = sorted(items, key=itemgetter(0))
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        if g.system_config.UseRefEmptyValue:
            items.insert(1, (-1, EMPTY_REFERENCE_VALUE,))
        return items

    def ref_activity_dates(self):
        args = { 'local_node':self.local_node[0] }
        items = []
        items += [(x.date, x.date) for x in get_activity_dates(args)]
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        return items

    def ref_messages_dates(self):
        args = { 'local_node':self.local_node[0] }
        items = []
        items += [(x.date, x.date) for x in get_messages_dates(args)]
        items.insert(0, (0, DEFAULT_UNDEFINED,))
        return items

    def run(self, page_title=None, data_title=None, **kw):
        return kw

    def response(self, **kw):
        pass
