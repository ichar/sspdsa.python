# -*- coding: utf-8 -*-

from operator import itemgetter

from ..settings import *
from ..pages import Divisions, Nodes, MessageTypes, Binds
from ..utils import (
     getToday
     )

from app.semaphore.views import initDefaultSemaphore


class PageRender:

    def __init__(self, page, template, database_config, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('PageRender init')

        self.page = page
        self.template = template
        self.database_config = database_config

        self.config = self.database_config.get(self.template) or {}

        self.divisions = None
        self.nodes = None
        self.messagetypes = None
        self.binds = None

    def _init_state(self, engine, args=None, factory=None, **kwargs):
        if IsDeepDebug:
            print('PageRender initstate')

        self.engine = engine
        self.args = args
        self.factory = factory

    def make_divisions(self, page_title, data_title, kw, with_make=None, params=None):
        action = None
        link = None

        if with_make is None:
            divisions = Divisions(self.page, self.database_config)
            divisions._init_state(self.engine)
            self.divisions = divisions
        if with_make is None or with_make:
            self.divisions.make(page_title, data_title, action, link, kw, params=params)

    def make_nodes(self, page_title, data_title, kw, with_make=None, params=None):
        action = None
        link = None

        if with_make is None:
            nodes = Nodes(self.page, self.database_config)
            nodes._init_state(self.engine)
            self.nodes = nodes
        if with_make is None or with_make:
            self.nodes.make(page_title, data_title, action, link, kw, params=params)

    def make_messagetypes(self, page_title, data_title, kw, with_make=None, params=None):
        action = None
        link = None

        if with_make is None:
            messagetypes = MessageTypes(self.page, self.database_config)
            messagetypes._init_state(self.engine)
            self.messagetypes = messagetypes
        if with_make is None or with_make:
            self.messagetypes.make(page_title, data_title, action, link, kw, params=params)

    def make_binds(self, page_title, data_title, kw, with_make=None, params=None):
        action = None
        link = None

        if with_make is None:
            binds = Binds(self.page, self.database_config)
            binds._init_state(self.engine)
            self.binds = binds
        if with_make is None or with_make:
            self.binds.make(page_title, data_title, action, link, kw, params=params)

    def run(self, page_title=None, data_title=None, **kw):
        self.make_divisions(page_title, data_title, kw)
        self.make_nodes(page_title, data_title, kw)
        self.make_messagetypes(page_title, data_title, kw)
        self.make_binds(page_title, data_title, kw)

        kw['page_title'] = page_title
        kw['data_title'] = data_title or ''
        kw['semaphore'] = initDefaultSemaphore()
        kw['style']['show_scroller'] = 1
        kw['navigation'] = get_navigation()
        kw['is_full_container'] = 1
        kw['is_no_line_open'] = 0
        kw['loader'] = url_for('references.loader')

        return kw
