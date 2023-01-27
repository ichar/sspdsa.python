# -*- coding: utf-8 -*-

import os
import sys
import codecs
import datetime
import traceback
import imp
import re

from collections import Iterable

basedir = os.path.abspath(os.path.dirname(__file__))
errorlog = os.path.join(basedir, 'traceback.log')

app_release = 1

# ----------------------------
# Global application constants
# ----------------------------

IsDebug                = 1  # sa[stdout]: prints general info (1 - forbidden with apache!)
IsDeepDebug            = 1  # sa[stdout]: prints detailed info (1 - forbidden with apache!)
IsTrace                = 1  # Trace[errorlog]: output execution trace for http-requests
IsSemaphoreTrace       = 0  # Trace[errorlog]: output trace for semaphore actions
IsLogTrace             = 1  # Trace[errorlog]: output detailed trace for Log-actions
IsTmpClean             = 1  # Flag: clean temp-folder
IsUseDecodeCyrillic    = 1  # Flag: sets decode cyrillic mode
IsUseDBLog             = 1  # Flag: sets DB OrderLog enabled to get log-messages
IsPrintExceptions      = 1  # Flag: sets printing of exceptions
IsForceRefresh         = 1  # Flag: sets http forced refresh for static files (css/js)
IsDecoderTrace         = 0  # Flag: sets decoder output
IsDisableOutput        = 0  # Flag: disabled stdout
IsFlushOutput          = 0  # Flag: flush stdout
IsShowLoader           = 0  # Flag: sets page loader show enabled
IsNoEmail              = 1  # Flag: don't send email
IsAppCenter            = 1  # Flag: KPTS-C application
IsAppBranch            = 1  # Flag: KPTS-O application
IsPublic               = 1  # Flag: Public application
IsFuture               = 0  # Flag: opens inactive future menu items
IsDemo                 = 0  # Flag: sets demo-mode (inactive)
IsPageClosed           = 0  # Flag: page is closed or moved to another address (page_redirect)

PUBLIC_URL = 'http://192.168.0.88:5000/'

page_redirect = {
    'items'    : ('*',),
    'base_url' : '/auth/onservice',
    'logins'   : ('admin',),
    'message'  : 'Waiting 30 sec',
}

LocalDebug = {
    'dbviewer'     : 0,
    'admlogviewer' : 0,
    'spologviewer' : 0,
    'configurator' : 0,
    'references'   : 0,
    'semaphore'    : 0,
    'equipment'    : 0,
    'center'       : 0,
    'branch'       : 0,
    'main'         : 0,
    'maintenance'  : 0,

}

LOCAL_FULL_TIMESTAMP   = '%d-%m-%Y %H:%M:%S'
LOCAL_EXCEL_TIMESTAMP  = '%d.%m.%Y %H:%M:%S'
LOCAL_EASY_TIMESTAMP   = '%d-%m-%Y %H:%M'
LOCAL_RUS_DATESTAMP    = '%d-%m-%Y'
LOCAL_EASY_DATESTAMP   = '%Y-%m-%d'
LOCAL_EXPORT_TIMESTAMP = '%Y%m%d%H%M%S'
UTC_FULL_TIMESTAMP     = '%Y-%m-%d %H:%M:%S'
UTC_EASY_TIMESTAMP     = '%Y-%m-%d %H:%M'
DATE_TIMESTAMP         = '%d/%m'
DATE_STAMP             = '%Y%m%d'

default_print_encoding = 'cp866'
default_unicode        = 'utf-8'
default_encoding       = default_unicode #'cp1251'
default_iso            = 'ISO-8859-1'

###default_system_locale  = 'en_US.UTF-8'
default_system_locale  = 'ru_RU.UTF-8'
default_chunk = 1000

# ---------------------------- #

DEFAULT_ROOT = {
    'local'  : 'http://127.0.0.1:5000/',
    'public' : '',
}

CONFIG_PATH = '/var/www/html/apps/sspdsa/orion/kpts.cfg'
####CONFIG_PATH = '/storage/www/apps/sspdsa/orion/kpts.cfg'

# ---------------------------- #

CONNECTION = {}


class ConnectionParams:

    def __init__(self):
        self._items = {
            'dialect'     : 'postgresql',
            'driver'      : 'psycopg2',
            'host'        : 'localhost',
            'database'    : 'sspds',
            'user'        : 'postgres',
            'password'    : 'admin',
            'scheme'      : 'orion',
            'timeout'     :  15, 
            'with_check'  :  0, 
            'encoding'    :  default_unicode,
            'options'     : '',
            'nsch'        : 0,
            'nkts'        : 0,
            'division'    : '',
            'node'        : '',
            'dayslog'     : 0,
            'attempt'     : 0,
            'answer'      : 0,
            'toprbd'      : 0,
            'system_path' : CONFIG_PATH
        }

        self._keys = {
            'dialect'     :  None,
            'driver'      :  None,
            'host'        : 'server_name',
            'database'    : 'database_name',
            'user'        : 'user_name',
            'password'    : 'admin',
            'scheme'      : 'schema_name',
            'timeout'     :  None, 
            'with_check'  :  None, 
            'encoding'    :  None,
            'options'     :  None,
            'nsch'        : 'nsch',
            'nkts'        : 'nkts',
            'dayslog'     : 'DAYSLOG',
            'attempt'     : 'n_attempt',
            'answer'      : 'timeout_kvt',
            'toprbd'      : 'toprbd',
            'system_path' : 'tasks_path'
        }

        self._update()

    def _update(self):
        self._items['options']  = 'options=-csearch_path=%(scheme)s' % self._items
        self._items['division'] = '%s%s' % (self._items['nsch'], self._items['nkts'])
        self._items['node'] = '%s_%s' % (self._items['nsch'], self._items['division'])

    def _init_state(self):
        self._mode = 'r'
        data = None

        with open(CONFIG_PATH, mode=self._mode) as _file:
            data = _file.read().strip()

        for item, key in [(key, self._keys[key]) for key in self._keys if self._keys[key] is not None]:
            if key is None:
                continue
            m = re.search(r'(([^\*\#]%s)=((.*)$))' % key, data, re.M)
            if m is not None and key == m.group(2).strip():
                self._items[item] = m.group(3).strip()

        del data
        data = None

        self._update()

    @property
    def dialect(self):
        return self._items.get('dialect')
    @property
    def driver(self):
        return self._items.get('driver')
    @property
    def host(self):
        return self._items.get('host')
    @property
    def database(self):
        return self._items.get('database')
    @property
    def user(self):
        return self._items.get('user')
    @property
    def password(self):
        return self._items.get('password')
    @property
    def scheme(self):
        return self._items.get('scheme')
    @property
    def database_timeout(self):
        return self._items.get('timeout')
    @property
    def with_check(self):
        return self._items.get('with_check')
    @property
    def encoding(self):
        return self._items.get('encoding')
    @property
    def options(self):
        return self._items.get('options')
    @property
    def nsch(self):
        return self._items.get('nsch')
    @property
    def nkts(self):
        return self._items.get('nkts')
    @property
    def division(self):
        return self._items.get('division')
    @property
    def node(self):
        return self._items.get('node')
    @property
    def forced_refresh_timeout(self):
        return int((self._items.get('toprbd') and self._items['toprbd'].isdigit() and int(self._items['toprbd']) or 30)*1.5)
    @property
    def dayslog(self):
        return int(self._items.get('dayslog') or 0)
    @property
    def socket_send_attempts(self):
        return int(self._items.get('attempt') or 0)
    @property
    def socket_answer_timeout(self):
        return int(self._items.get('answer') or 0)
    @property
    def system_path(self):
        return self._items.get('system_path')
    @property
    def local_node(self):
        return (self._items.get('nsch'), self._items.get('nkts'))
    @property
    def is_main(self):
        return self.division == '10'
    @property
    def items(self):
        return self._items

# ---------------------------- #

connection_params = ConnectionParams()
connection_params._init_state()

TIMEZONE = 'Europe/Moscow'
TIMEZONE_COMMON_NAME = 'Moscow'

SEMAPHORE_TEMPLATE = ''

if IsAppCenter:

    CONNECTION.update({
        'default'   : connection_params.items.copy(),
        'semaphore' : connection_params.items.copy(),
        'sspds'     : connection_params.items.copy(),
    })

    SEMAPHORE_TEMPLATE = 'none'

LOG_PATH = './logs'
LOG_NAME = 'app'

email_address_list = {}

# ---------------------------- #

ansi = not sys.platform.startswith("posix")

n_a = 'n/a'
cr = '\n'

def isIterable(v):
    return not isinstance(v, str) and isinstance(v, Iterable)

#######################################################################

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SQLALCHEMY_DATABASE_URI = None

    WTF_CSRF_ENABLED = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    sa = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
        "%(dialect)s+%(driver)s://%(user)s:%(password)s@%(host)s/%(database)s?%(options)s" % \
            connection_params.items

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        "%(dialect)s+%(driver)s://%(user)s:%(password)s@%(host)s/%(database)s?%(options)s" % \
            connection_params.items

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = { \
    'development': DevelopmentConfig,
    'production' : ProductionConfig,

    'default'    : DevelopmentConfig,
}

##  --------------------------------------- ##

def setup_console(sys_enc=default_unicode):
    pass

def print_to(f, v, mode='ab', request=None, encoding=default_encoding):
    if IsDisableOutput:
        return
    items = not isIterable(v) and [v] or v
    if not f:
        f = getErrorlog()
    fo = open(f, mode=mode)
    def _out(s):
        if not isinstance(s, bytes):
            fo.write(s.encode(encoding, 'ignore'))
        else:
            fo.write(s)
        fo.write(cr.encode())
    for text in items:
        try:
            if IsDeepDebug:
                print(text)
            if request is not None:
                _out('%s>>> %s [%s]' % (cr, datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP), request.url))
            _out(text)
        except Exception as e:
            pass
    fo.close()

def print_exception(stack=None):
    print_to(errorlog, '%s>>> %s:%s' % (cr, datetime.datetime.now().strftime(LOCAL_FULL_TIMESTAMP), cr))
    traceback.print_exc(file=open(errorlog, 'a'))
    if stack is not None:
        print_to(errorlog, '%s>>> Traceback stack:%s' % (cr, cr))
        traceback.print_stack(file=open(errorlog, 'a'))

def getErrorlog():
    return errorlog

def getCurrentDate():
    return datetime.datetime.now().strftime(LOCAL_EASY_DATESTAMP)


if __name__ == "__main__":
    connection_params._init_state()
