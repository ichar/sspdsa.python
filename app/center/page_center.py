# -*- coding: utf-8 -*-

import re
from copy import deepcopy
from operator import itemgetter

from config import LOCAL_EASY_DATESTAMP, LOCAL_EASY_TIMESTAMP, DATE_STAMP, default_chunk

from ..settings import *
from ..models import Division, Node, MessageType, Bind, Line, LineState, Message, get_center_messages_period
from ..pages import Messages
from ..utils import (
     getToday, getDate, getDateOnly, getString, getSQLString,
     checkPaginationRange, Capitalize, unCapitalize, cleanHtml
     )

from .page_default import (
      clean, check_int, check_line, get_line, get_item_code, get_line_id, 
      PageRender
      )

from app.semaphore.views import initDefaultSemaphore


##  ===================
##  PageCenter Model
##  ===================

default_page = 'center'
default_locator = 'center'
default_template = 'messages'

_PAGE_LINK = ('%scenter', '?sidebar=0',)

## ==================================================== ##

_config = {}

## ==================================================== ##


class PageCenter(PageRender):
    
    def __init__(self, page, template, database_config, **kw):
        if IsDeepDebug:
            print('PageCenter init')

        super().__init__(page, template, database_config, **kw)

        self._model = 0
        self._distinct = True

        self.period = (None, None)

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageCenter initstate')

        super()._init_state(engine, args, factory)

        self._messages = None
        self._capacities = None
        self._speeds = None

        self.prepare()

    @property
    def filter_items(self):
        return {
            'selected_date' : (self._selected_date, 'selected_date'),
            #'selected_division' : (self.selected_division, 'selected_division'),
            'selected_line' : (self._selected_line, 'selected_line'),
            'search' : (self._search, 'search'),
        }
    @property
    def is_valid(self):
        return True

    #   ------------
    #   PAGE FILTERS
    #   ------------

    def get_current_filter(self):
        return ''.join([self.get_selected_date(), self.get_selected_line(), self.get_search()])

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
        self.set_selected_line()

        self._filter_items = {
            'selected_date' : (self._selected_date, 'selected_date'),    
            'selected_line' : (self._selected_line, 'selected_line'),
            'local_node' : (self._local_node, 'local_node'),
            'search' : (self._search, 'search'),
        }

    def response(self, **kw):
        return self._messages.response

    #   ------
    #   CUSTOM
    #   ------

    def dates(self):
        pass

    def get_period(self):
        self.period = get_center_messages_period()
        return '%s - %s' % (getDate(self.period[0], LOCAL_EASY_TIMESTAMP), getDate(self.period[1], LOCAL_EASY_TIMESTAMP))

    def make_messages(self, page_title, data_title, kw, with_make=None, params=None):
        action = request.path
        link = None
        name = 'messages'
        template = 'messages'

        kw['period'] = self.get_period()
        args = self.query

        if with_make is None:
            messages = Messages(self.page, self.database_config, name=name, template=template)
            messages._init_state(self.engine, args=args, action=action, is_gen=True, with_chunks=0)
            messages.set_current_filter(self.get_current_filter())
            self._messages = messages
        if with_make is None or with_make:
            self._messages.make(page_title, data_title, action, link, kw, 
                row_iter=self.row_messages_iter, cls=self.map_lines, 
                params=params
                )

        # ID
        # id
        # pk
        # np
        # selected
        # ------------------------------------------------
        # pk messagetype size login 
        # sent received r1 r2 dater1 dater2 
        # node sender receiver before after 
        # kuo kuoo kuop kuopr kuosl ns ksb kuo kuoo kuop kuopr kuosl

        rows = self._messages.view.rows
        total_rows = self._messages.view.total_rows
        
        return

    @staticmethod
    def row_messages_iter(cls, row, args):
        if row is None or row.kuo is None or row.kuoo is None or row.kuop is None:
            return None

        #code = get_line_id(row.kuoo, row.kuop)
        #item = cls.get(code)

        #if not check_query_division(args, row.kuoo, row.kuop):
        #    return None

        item_id = item and get_item_id(sender, receiver)
        item = {
            'ID'          : row.pk,
            'MESSAGETYPE' : row.messagetype,
            'NUMBER'      : row.number,
            'LOGIN'       : row.login,
            'SIZE'        : row.size, 
            'NODE'        : row.node, 
            'SENDER'      : row.sender, 
            'RECEIVER'    : row.receiver, 
            'BEFORE'      : row.before, 
            'AFTER'       : row.after,
            'SENT'        : getDate(row.sent, LOCAL_EASY_TIMESTAMP),
            'RECEIVED'    : getDate(row.received, LOCAL_EASY_TIMESTAMP),
            'R1'          : row.r1,
            'R2'          : row.r2,
            'DATER1'      : getDate(row.dater1, LOCAL_EASY_TIMESTAMP),
            'DATER2'      : getDate(row.dater2, LOCAL_EASY_TIMESTAMP),
        }
        return item

    def make_capacities(self, page_title, data_title, kw, with_make=None, params=None):
        action = request.path
        link = None
        name = 'capacities'
        template = 'capacities'

        kw['period'] = self.get_period()

        if with_make is None:
            capacities = Messages(self.page, self.database_config, name=name, template=template)
            capacities._init_state(self.engine, args=self.query, action=action, is_gen=True, with_chunks=default_chunk)
            self._capacities = capacities
        if with_make is None or with_make:
            self._capacities.make(page_title, data_title, action, link, kw, 
                row_iter=self.row_capacities_iter, cls=self.map_lines, 
                params=params
                )

        # ID
        # id
        # pk
        # np
        # selected
        # --------------------------------
        # node messagetype capacity volume

        rows = self._capacities.view.rows
        total_rows = self._capacities.view.total_rows
        
        return

    @staticmethod
    def row_capacities_iter(cls, row, vrows, args):
        if row is None or row.node is None:
            return None
        pk = row.node
        node = 'N-%s' % row.node
        mtype = 'T-%s' % row.mtype
        line = row.line
        messagetype = row.messagetype
        """
        item = {
            'ID'          : pk,
            'LINE'        : line,
            'mtype' : {
                'MESSAGETYPE' : messagetype,
                'capacity'    : [0, 0],
                'volume'      : 0,
                'VALUE'       : '',
                'order'       : '',
            }
            'TOTAL'       : 0,
            'VOLUME'      : 0
        }
        """
        if 'TOTAL' not in vrows:
            vrows['TOTAL'] = Messages.set_capacity_messagetype(('T-0', '= Всего', 0, 0, 'TOTAL'))

        if node not in vrows:
            vrows[node] = Messages.set_capacity_messagetype((pk, line, 0, 0, node))

        is_update = False
        for key in (node, 'TOTAL'):
            is_total = key == 'TOTAL'
            vrow = vrows[key]
            if mtype not in vrow:
                vrow[mtype] = Messages.set_messagetype_column(messagetype)
                is_update = True
            else:
                is_update = is_total

            vcolumn = vrow[mtype]
    
            capacity = [int(x) for x in row.capacity.split('-')]
            volume = [int(x) for x in row.volume.split('-')]
    
            if is_update:
                Messages.set_capacity(vcolumn, capacity, volume, is_total)
    
            vrow['TOTAL'] += max(capacity)
            vrow['VOLUME'] += sum(volume)
            vrow['css'] = is_total and 'TOTAL' or ''

        return 1

    def make_speeds(self, page_title, data_title, kw, with_make=None, params=None):
        action = request.path
        link = None
        name = 'speeds'
        template = 'speeds'

        kw['period'] = self.get_period()

        if with_make is None:
            speeds = Messages(self.page, self.database_config, name=name, template=template)
            speeds._init_state(self.engine, args=self.query, action=action, is_gen=True, with_chunks=default_chunk)
            self._speeds = speeds
        if with_make is None or with_make:
            self._speeds.make(page_title, data_title, action, link, kw, 
                row_iter=self.row_speeds_iter, cls=self.map_lines, 
                params=params
                )

        # ID
        # id
        # pk
        # np
        # selected
        # ---------------------------
        # node line volume time speed

        rows = self._speeds.view.rows
        total_rows = self._speeds.view.total_rows
        
        return

    @staticmethod
    def row_speeds_iter(cls, row, vrows, args):
        if row is None or row.node is None:
            return None
        pk = row.node
        node = 'N-%s' % row.node
        line = row.line
        """
        item = {
            'ID'          : pk,
            'LINE'        : line,
            'VOLUME'      : 0,
            'TIME'        : 0,
            'VALUE'       : 0,
            'TOTAL'       : 0,
            'ERRORS'      : 0,
        }
        """
        if 'TOTAL' not in vrows:
            vrows['TOTAL'] = Messages.set_speed_type(('T-0', '= Всего', 0, 0, '', 0, 0, 'TOTAL'))

        is_update = False
        for key in (node, 'TOTAL'):
            is_total = key == 'TOTAL'
            if key not in vrows:
                vrows[key] = Messages.set_speed_type((node, line, 0, 0, '', 0, 0, node))
                is_update = True
            else:
                is_update = is_total

            vrow = vrows[key]

            speed = row.speed and float(row.speed) or 0.0
            time = row.time and float(row.time) or 0.0
            volume = row.volume and int(row.volume) or 0.0
            errors = row.errors and int(row.errors) or 0

            if is_update:
                Messages.set_speed(vrow, speed, volume, time, errors, is_total)
    
            vrow['TOTAL'] = round(vrow['speed'], 2)

            vrow['css'] = ' '.join(list(filter(None, [is_total and 'TOTAL' or None, vrow['errors'] and 'ERROR' or None]))) or ''

        return 1

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

    def run(self, page_title, data_title, action, link, **kw):
        self.make_messages(page_title, data_title, kw)
        self.make_capacities(page_title, data_title, kw)
        self.make_speeds(page_title, data_title, kw)

        """
        kw['data_title'] = data_title or ''
        kw['semaphore'] = initDefaultSemaphore()
        kw['style']['show_scroller'] = 1
        kw['navigation'] = get_navigation()
        kw['is_full_container'] = 1
        kw['is_no_line_open'] = 0
        kw['loader'] = url_for('center.loader')
        kw['action'] = action
        kw['link'] = link
        """
        return kw

