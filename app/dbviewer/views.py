# -*- coding: utf-8 -*-

import sys
import os
import re

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from sqlalchemy import MetaData, create_engine

from config import (
     CONNECTION,
     IsDebug, IsDeepDebug, IsTrace, IsUseDecodeCyrillic, IsUseDBLog, IsPrintExceptions, IsDecoderTrace, LocalDebug,
     basedir, errorlog, print_to, print_exception,
     default_print_encoding, default_unicode, default_encoding, default_iso, cr,
     LOCAL_EXCEL_TIMESTAMP, LOCAL_EASY_DATESTAMP, LOCAL_EXPORT_TIMESTAMP, UTC_FULL_TIMESTAMP, DATE_STAMP, 
     email_address_list
     )

from . import dbviewer

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, getDateOnly, checkDate, del_file, spent_time, cdate, indentXMLTree, isIterable, 
     makeCSVContent, makeXLSContent, makeIDList, decoder, 
     checkPaginationRange, getParamsByKeys, pickupKeyInLine,
     default_indent, Capitalize, sint, image_base64, normpath, fromtimestamp, daydelta, rfind
     )


##  ==================================
##  Database View Presentation Package
##  ==================================

default_page = 'dbviewer'
default_action = '300'
default_log_action = '301'
default_template = 'changes'


# Локальный отладчик
IsLocalDebug = LocalDebug[default_page]
# Использовать OFFSET в SQL запросах
IsApplyOffset = 1
# Принудительная загрузка статических файлов
IsForceRefresh = 0
IsPrintPsycopg = 0
IsPrintAlchemy = 1


def before(f):
    def wrapper(**kw):
        connection = kw.get('connection')
        name = None
        if not connection:
            name = kw.get('engine') or 'default'
            connection = CONNECTION.get(name)
        g.engine = DatabaseEngine(name=name, user=g.current_user, connection=connection)
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.requested_object = {}

## ==================================================== ##

def print_msg(msg):
    pass #print('%s %s:' % ('-'*20, msg))

def getMetadata(sql):
    #ps_cursor = g.engine.conn.cursor(cursor_factory=RealDictCursor)
    ps_cursor = g.engine.execute(sql)
    headers = [key for key in ps_cursor._metadata.keys]
    if IsDebug:
        print(headers)
    return headers

def getData(sql, headers):
    print_msg('SQLAlchemy')

    res = g.engine.conn.execute(sql)
    data = res.fetchall()
    if IsDebug:
        print(len(data))

    rows = []
    for n, line in enumerate(data):
        if IsPrintAlchemy:
            #print('>>> %d %s' %(n, line))
            #print('>>> row %d ' % n)
            row = {}
            for i, value in enumerate(line):
                column = headers[i]
                row[column] = value
                #print('>%d[%s]:%s' % (i, column, str(value).strip()))

            rows.append(row)

    if IsDeepDebug:
        #print('type data: %s' % type(data))
        #print('type row: %s' % type(data[0]))
        #print(data[0])
        pass

    return rows


def getCursor(sql):
    rows = []
    print_msg('psycopg')
    with ps_conn:
        with ps_conn.cursor() as cursor:
            cursor.execute(sql)
            headers = [desc[0] for desc in cursor.description]
            for n, line in enumerate(cursor):
                if IsPrintPsycopg:
                    print('>>> row %d ' % n)
                row = {}
                for i, value in enumerate(line):
                    column = headers[i]
                    row[column] = value
                    if IsPrintPsycopg:
                        print('>%d[%s]:%s' % (i,headers[i], str(value).strip())) #
                rows.append(row)

    return rows

## ==================================================== ##

@dbviewer.route('/<view>', defaults={'as_type': 'dict'}, methods = ['GET'])
@dbviewer.route('/<view>/<as_type>', methods = ['GET'])
@login_required
def data_viewer(view, as_type, **kw):
    connection = CONNECTION[kw.get('engine') or 'sspds']

    if IsDebug:
        print_to(None, '>>> dbviewer: connection %s' % connection)

    refresh(connection=connection)

    where = ''
    order = ''
    limit = 100

    sql = 'SELECT * FROM %s %s %s %s' % (
        view,
        where and ('WHERE %s ' % where) or '',
        order and ('ORDER BY %s ' % order) or '',
        limit and ('LIMIT %s ' % limit) or '',
    )
    if IsDeepDebug:
        print('>>> dbviewer: SQL %s, view: %s, a_type: %s' % (sql, view, as_type))

    if IsDebug:
        print_to(None, '>>> SQL: %s' % sql, encoding=default_encoding)

    headers = getMetadata(sql)
    rows = getData(sql, headers)

    kw = { 
        'title'        : 'dbviewer',
        'connection'   : connection,
        'config'       : database_config,
        'view'         : view, 
        'as_type'      : as_type,
        'headers'      : headers,
        'rows'         : rows,
        'sql'          : sql,
        'total_columns': len(headers),
        'total_rows'   : len(rows),
    }
    return render_template('dbviewer.html', **kw)


@dbviewer.route('/', methods = ['GET'])
@dbviewer.route('/index', methods = ['GET','POST'])
def start():
    try:
        return index()
    except:
        raise

def index():
    debug, kw = init_response('Application DBviewer Page')
    kw['product_version'] = product_version

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

    command = get_request_item('command')


@dbviewer.after_request
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
