# -*- coding: utf-8 -*-

import os
import sys
import codecs
import datetime
import traceback
import imp

from collections import Iterable

basedir = os.path.abspath(os.path.dirname(__file__))
errorlog = os.path.join(basedir, 'traceback.log')

app_release = 1

# ----------------------------
# Global application constants
# ----------------------------

IsDebug                = 1  # sa[stdout]: prints general info (1 - forbidden with apache!)
IsDeepDebug            = 0  # sa[stdout]: prints detailed info (1 - forbidden with apache!)
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
default_encoding       = 'cp1251'
default_iso            = 'ISO-8859-1'

default_system_locale  = 'en_US.UTF-8' # 'ru_RU.UTF-8'

# ---------------------------- #

connection_params = {
        'dialect'   : 'postgresql',
        'driver'    : 'psycopg2',
        'host'      : 'localhost',
        'database'  : 'sspds',
        'user'      : 'postgres',
        'password'  : 'admin',
        'schema'    : 'orion',
        'timeout'   :  15, 
        'with_check':  0, 
        'encoding'  :  default_unicode,
}

connection_params['options'] = 'options=-csearch_path=%(schema)s' % connection_params

TIMEZONE = 'Europe/Moscow'
TIMEZONE_COMMON_NAME = 'Moscow'

CONNECTION = {}

SEMAPHORE_TEMPLATE = ''

if IsAppCenter:
    CONNECTION.update({
        'default'   : connection_params.copy(),
        'semaphore' : connection_params.copy(),
        'sspds'     : connection_params.copy(),
    })
    SEMAPHORE_TEMPLATE = 'none'

DEFAULT_ROOT = {
    'local'  : 'http://127.0.0.1:5000/',
    'public' : '',
}
LOG_PATH = './logs'
LOG_NAME = 'app'

#CONFIG_PATH = '/var/www/html/apps/sspdsa/orion/kpts.cfg'
CONFIG_PATH = 'storage/www/apps/sspdsa/orion/kpts.cfg'

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

    WTF_CSRF_ENABLED = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    sa = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        "%(dialect)s+%(driver)s://%(user)s:%(password)s@%(host)s/%(database)s?%(options)s" % connection_params
        #'sqlite:///' + os.path.join(basedir, 'storage', 'app.db.new')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        "%(dialect)s+%(driver)s://%(user)s:%(password)s@%(host)s/%(database)s?%(options)s" % connection_params # %%3D

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = { \
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
