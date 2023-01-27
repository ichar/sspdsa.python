# -*- coding: utf-8 -*-

import re
from copy import deepcopy
from operator import itemgetter

from config import LOCAL_EASY_DATESTAMP, LOCAL_EASY_TIMESTAMP, DATE_STAMP, default_chunk

from ..settings import *
from ..models import Division, Node, MessageType, Bind, Line, LineState, get_linestates_period, nodes_forced_refresh
from ..pages import Nodes, Lines, LineStates
from ..utils import (
     getToday, getDate, getDateOnly, getTimedelta, isTimedelta,
     checkPaginationRange, Capitalize, unCapitalize, cleanHtml
     )

from .page_default import (
      clean, check_int, check_line, get_line, get_item_code, get_line_id, 
      PageRender
      )

from app.semaphore.views import initDefaultSemaphore


##  ===================
##  PageEquipment Model
##  ===================

default_page = 'equipment'
default_locator = 'equipment'
default_template = 'equipment-orders'

_PAGE_LINK = ('%sequipment', '?sidebar=0',)

## ==================================================== ##

_config = {
}

## ==================================================== ##


def show_state(node_state, line_state):
    return { 'suo' : check_int(node_state), 'ssd': check_int(line_state) }

def is_large(x1, x2):
    a = x1.split('_')
    b = x1.split('_')
    return a[0] > b[0] or a[1] > b[1]

def get_item_id(node1, node2):
    x1 = get_item_code(node1)
    x2 = get_item_code(node2)
    if is_large(x1, x2):
        x1, x2 = x2, x1
    else:
        x2, x1 = x1, x2
    x = '%s-%s%s' % (x1, x2, 
        (node2.nsch == 1 and node2.nkts == 0 and node1.nsch in (2,3,4) and node1.nkts == 0 and '-1_2') or
        (node1.nsch == 1 and node1.nkts == 0 and node2.nsch in (2,3,4) and node2.nkts == 0 and '-1_2') or 
        '')
    return clean(x)

def check_query_division(args, node1, node2):
    division = args and args.get('selected_division') or None
    if division is not None:
        selected_division = division - 1
    else:
        selected_division = None
    if selected_division is not None and selected_division > -1:
        if selected_division not in (node1.nsch, node2.nsch):
            return False
    return True


class ItemNode:
    def __init__(self, ob, xdivisions):
        self.kuo = ob.kuo
        self.nsch = ob.nsch
        self.nkts = ob.nkts
        self.pk = ob.kuo
        self.ob = ob
        self.code = '%s%s' % (self.nsch, self.nkts)
        self.name = '%s:%s' % (xdivisions[ob.nsch]['NAME'], ob.kikts)
        self.node = get_item_code(self)
        self.id = self.node
        self.state = ob.suo


class ItemLine:
    def __init__(self, node1, node2, xlines):
        self.is_valid = 1
        self.params = []
        self.code = get_line_id(node2.kuo, node1.kuo)
        self.ob = xlines.get(self.code)

        if self.ob is None:
            self.id = self.code
            self.is_valid = 0
            return

        self.state = self.ob.ssd
        self.pk = self.ob.ksd
        self.line = get_item_id(node1, node2)
        self.id = self.line
        self.node1 = node1
        self.node2 = node2


class PageEquipment(PageRender):

    def __init__(self, default_page, default_template, database_config, **kw):
        if IsDeepDebug:
            print('PageEquipment init')

        super().__init__(default_page, default_template, database_config, **kw)

        self._model = 0
        self._distinct = True

        self.period = (None, None)

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageEquipment initstate')

        super()._init_state(engine, args, factory)

        self._activities = None
        self._reliabilities = None

        self.prepare()

    @property
    def activities(self):
        return self._activities
    @property
    def reliabilities(self):
        return self._reliabilities
    @property
    def filter_items(self):
        return {
            'selected_date' : (self.selected_date, 'selected_date'),
            'selected_division' : (self.selected_division, 'selected_division'),
            'selected_line' : (self.selected_line, 'selected_line'),
            'search' : (self.search, 'search'),
        }
    @property
    def is_valid(self):
        return True

    #   ------------
    #   PAGE FILTERS
    #   ------------

    def get_current_filter(self):
        return ''.join([self.get_selected_date(), self.get_selected_division(), self.get_selected_line(), self.get_search()])

    #   --------
    #   HANDLERS
    #   --------

    def prepare(self):
        super().prepare()

    def render(self, **kw):
        super().render(**kw)

        # ----------------------
        # Условия отбора записей
        # ----------------------

        self.set_selected_date()
        self.set_selected_division()
        self.set_selected_line()

        self._filter_items = {
            'selected_date' : (self._selected_date, 'selected_date'),    
            'selected_division' : (self._selected_division, 'selected_division'),
            'selected_line' : (self._selected_line, 'selected_line'),
            'local_node' : (self._local_node, 'local_node'),
            'search' : (self._search, 'search'),
        }

    def response(self, **kw):
        pass

    #   ------
    #   CUSTOM
    #   ------

    def get_period(self):
        self.period = get_linestates_period()
        return '%s - %s' % (getDate(self.period[0], LOCAL_EASY_TIMESTAMP), getDate(self.period[1], LOCAL_EASY_TIMESTAMP))

    def make_activities(self, page_title, data_title, kw, with_make=None, params=None):
        action = request.path
        link = None
        name = 'activities'
        template = 'activities'

        kw['period'] = self.get_period()

        if with_make is None:
            activities = LineStates(self.page, self.database_config, name=name, template=template)
            activities._init_state(self.engine, args=self.query, action=action, is_gen=True, with_chunks=default_chunk)
            self._activities = activities
        if with_make is None or with_make:
            self._activities.make(page_title, data_title, action, link, kw, row_iter=self.row_activities_iter, cls=self.map_lines, params=params)

        # ID
        # LINE
        # NDIV-1
        # NDIV-2
        # STATE
        # CHECKED
        # id
        # pk
        # np
        # selected
        # --------------------------------------------------------
        # date ksd kuo kuov ssd node1 node2 line is_error metadata

        rows = self._activities.view.rows
        total_rows = self._activities.view.total_rows
        
        return

    @staticmethod
    def row_activities_iter(cls, row, args):
        if row is None or row.kuo is None or row.kuov is None:
            return None

        code = get_line_id(row.kuo, row.kuov)
        item = cls.get(code)
        node1 = getattr(item, 'node1')[0]
        node2 = getattr(item, 'node2')[0]

        if not check_query_division(args, node1, node2):
            return None

        item_id = item and get_item_id(node1, node2)
        if not item_id:
            return None

        item = {
            'ID'      : code,
            'id'      : item_id,
            'PK'      : row.ksd,
            'CODE'    : row.code,
            'NDIV-1'  : row.kuo,
            'NDIV-2'  : row.kuov,
            'NODE-1'  : row.node1,
            'NODE-2'  : row.node2,
            'LINE'    : get_line(row.node1, row.node2),
            'STATE'   : row.ssd == 1 and 'Вкл' or 'Выкл',
            'CHECKED' : getDate(row.date, LOCAL_EASY_TIMESTAMP),
        }
        if row.ssd:
            item['Ready'] = True
        else:
            item['Error'] = True
        return item

    def make_reliabilities(self, page_title, data_title, kw, with_make=None, params=None):
        action = request.path
        link = None
        name = 'reliabilities'
        template = 'reliabilities'

        if with_make is None:
            reliabilities = LineStates(self.page, self.database_config, name=name, template=template)
            reliabilities._init_state(self.engine, args=self.query, action=action)
            self._reliabilities = reliabilities
        if with_make is None or with_make:
            period = [getTimedelta(self.period[1] - self.period[0], 0), getTimedelta(self.period[0], 0), getTimedelta(self.period[1], 0)]
            self._reliabilities.make(page_title, data_title, action, link, kw, 
                row_iter=self.row_reliabilities_iter, cls=self.map_lines, period=period, 
                params=params)

        # ID
        # LINE
        # NDIV-1
        # NDIV-2
        # STATE
        # CHECKED
        # id
        # pk
        # np
        # selected
        # --------------------------------------------------------
        # date ksd kuo kuov ssd node1 node2 line is_error metadata

        rows = self._reliabilities.view.rows
        total_rows = self._reliabilities.view.total_rows
        
        return

    @staticmethod
    def row_reliabilities_iter(cls, row, rows, args):
        if row is None or row.kuo is None or row.kuov is None:
            return

        code = get_line_id(row.kuo, row.kuov)
        item = cls.get(code)
        node1 = getattr(item, 'node1')[0]
        node2 = getattr(item, 'node2')[0]

        if not check_query_division(args, node1, node2):
            return None

        item_id = item and get_item_id(getattr(item, 'node1')[0], getattr(item, 'node2')[0])
        if not item_id:
            return None

        date = row.date
        state = row.ssd

        if code not in rows:
            rows[code] = {
                'ID' : row.ksd,
                'id' : item_id,
                'CODE': code, 
                'STATE0' : 0, 
                'STATE1' : 0, 
                'ON' : 0, 
                'OFF' : 0, 
                'LINE' : get_line(row.node1, row.node2),
                'VALUE' : 0,
                'is_off' : False,
                'is_on' : False,
                }

        item = rows[code]
        if date:
            if not state:
                if item['STATE1']:
                    item['ON'] += getTimedelta(date, item['STATE1'])
                    item['STATE1'] = 0
                elif item['STATE0']:
                    item['OFF'] += getTimedelta(date, item['STATE0'])
                elif not item['is_off']:
                    item['OFF'] += getTimedelta(date, 0)
                    item['is_off'] = True
                elif not item['is_on']:
                    item['ON'] += getTimedelta(date, 0)
                    item['is_on'] = True
                item['STATE0'] = date
            else:
                if item['STATE1']:
                    item['ON'] += getTimedelta(date, item['STATE1'])
                elif item['STATE0']:
                    item['OFF'] += getTimedelta(date, item['STATE0'])
                    item['STATE0'] = 0
                elif not item['is_on']:
                    item['ON'] += getTimedelta(date, 0)
                    item['is_on'] = True
                elif not item['is_off']:
                    item['OFF'] += getTimedelta(date, 0)
                    item['is_off'] = True
                item['STATE1'] = date

    @staticmethod
    def box_color(node_state, line_state):
        return node_state == 2 and 'bred' or node_state == 1 and 'bgreen' or 'byellow'
    @staticmethod
    def box_border(node_state):
        return node_state in (1,2) and 'bb-bw' or 'bw-bb'
    @staticmethod
    def line_color(node_state, line_state):
        return node_state == 2 and 'lred' or  node_state == 1 and (line_state== 0 and 'lred' or line_state== 1 and 'lgreen') or 'lyellow'

    def set_node_info(self, node, nodes):
        items = self.nodes[0]
        if not node:
            return
        code = node.code
        pk = node.pk
        nsch = node.nsch
        key = 'item_%s' % node.id
        if key not in nodes:
            item = items.get(pk)
            nodes[key] = {
                'ID'   : code,
                'pk'   : pk ,
                'nsch' : nsch,
                'code' : code, 
                'name' : check_line('%s:%s[%s]' % (item['DIVISION'], item['NAME'], item['FULLNAME'])),
                'ip'   : item['IP'] or g.maketext('none'),
                'port' : '%s' % (item['PORT1'] and item['PORT2'] and '%s:%s' % (item['PORT1'], item['PORT2']) or g.maketext('none')),
                }

    def get_items(self, cls, key):
        source = cls.ordered_rows()
        rows = cls.get_rows(self.database_config[key], obs=source)
        return dict([(x['ID'], x) for x in rows]), source

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

    def render_diagram(self):
        props = {}

        def line_is_exist(ob, node):
            code = ob is not None and get_line_id(ob.kuo or 0, node.kuo or 0) or '...'
            return code in self.map_lines

        def find_node(ob):
            for line in self.ordered_lines:
                if line.kuo == ob.kuo:
                    x =  getattr(line, 'node2')
                    if x is not None and isinstance(x[0], Node):
                        return x[0]
            return None

        nodes = {}
        boxes = {}
        lines = {}
        node = None
        node2 = None
        n = 0
        l = 0
        plines = []
        pnodes = []
        for ob in self.ordered_nodes:
            if node is None:
                node = ItemNode(ob, self.source_divisions)
            elif node2 is not None and ob.uruo in (node2.ob.uruo, node2.ob.uruo+1) and line_is_exist(ob, node2):
                node = ItemNode(ob, self.source_divisions)
            elif ob.uruo in (node.ob.uruo, node.ob.uruo+1) and line_is_exist(ob, node):
                node2 = deepcopy(node)
                node = ItemNode(ob, self.source_divisions)
            elif ob.uruo == 3:
                if node2 is not None and line_is_exist(ob, node2):
                    node = ItemNode(ob, self.source_divisions)
                else:
                    x = find_node(ob)
                    if x is not None and line_is_exist(ob, x):
                        node2 = ItemNode(x, self.source_divisions)
                        node = ItemNode(ob, self.source_divisions)
                    else:
                        node2 = None
            else:
                node2 = None

            if node is not None and node2 is not None:
                n += 1
                pnodes.append('... pnodes:%s pk:%s code:%s id:%s-%s name[%s:%s]' % (
                    n, (node.pk, node2.pk), (node.code, node2.code), node.id, node2.id, node.name, node2.name))
            else:
                pnodes.append('... pnodes undefined node1:%s node2: %s' % (node and node.code, node2 and node2.code))

            if node2 is None:
                continue

            line = ItemLine(node2, node, self.map_lines)

            l += 1
            if line.is_valid:
                plines.append('... pline:%s pk[%s] code[%s] id[%s] state:%s valid:%s' % (
                    l, line.pk, line.code, line.id, line.state, line.is_valid))
            else:
                plines.append('... pline:%s[%s] invalid' % (l, line.code))

            if line.is_valid:
                if node.id not in boxes:
                    state = show_state(node.state, line.state)
                    boxes[node.id] = [self.box_color(node.state, line.state), self.box_border(node.state), state]
                    self.set_node_info(node, nodes)
                if node2.id not in boxes:
                    state = show_state(node2.state, line.state)
                    boxes[node2.id] = [self.box_color(node2.state, line.state), self.box_border(node2.state), state]
                    self.set_node_info(node2, nodes)
                    
                if isinstance(line.params, list):
                    state = show_state(line.node1.state, line.state)
                    color = self.line_color(line.node1.state, line.state)
                    line.params.append(color)
                    line.params.append(state)

                lines[line.id] = line.params
            else:
                boxes[node.id] = None
                lines[line.id] = 'invalid:[%s]' % line.code

        if IsDeepDebug:
            print_to(None, '>>> LINES [kuo|kuov]:')
            for node in pnodes:
                print_to(None, node)
            print_to(None, '...')
            print_to(None, '>>> LINES [state]:')
            for line in plines:
                print_to(None, line)
            print_to(None, '...')

        props['period'] = self.get_period()
        props['nodes'] = nodes
        props['boxes'] = boxes
        props['lines'] = lines

        if IsDebug:
            print_to(None, '>>> DIVISION NODES:')
            for node in nodes:
                print_to(None, '... node:%s %s' % (node, nodes[node]))
            print_to(None, '...')
            print_to(None, '>>> DIAGRAM BOXES:')
            for box in boxes:
                print_to(None, '... box:%s %s' % (box, boxes[box]))
            print_to(None, '...')
            print_to(None, '>>> DIAGRAM LINES:')
            for line in lines:
                print_to(None, '... line:%s %s' % (line, lines[line]))
            print_to(None, '...')

        return props

    def forced_refresh(self):
        nsch = connection_params.nsch
        nkts = connection_params.nkts
        timedelta = connection_params.forced_refresh_timeout

        return nodes_forced_refresh(nsch=nsch, nkts=nkts, state=1, timedelta=timedelta)

    def run(self, page_title=None, data_title=None, **kw):
        self.make_activities(page_title, data_title, kw)
        self.make_reliabilities(page_title, data_title, kw)

        #action = kw['activities']['pagination']['action']

        kw['page_title'] = page_title
        kw['data_title'] = data_title or ''
        kw['semaphore'] = initDefaultSemaphore()
        kw['style']['show_scroller'] = 1
        kw['navigation'] = get_navigation()
        kw['is_full_container'] = 1
        kw['is_no_line_open'] = 0
        kw['loader'] = url_for('main.loader')

        return kw

