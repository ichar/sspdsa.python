# -*- coding: utf-8 -*-

import datetime
import codecs
import sys
import os
import re
import time
from operator import itemgetter

from config import (
     basedir, 
     IsDebug, IsDeepDebug, IsTrace, IsLogTrace, IsPrintExceptions, IsDisableOutput,
     UTC_FULL_TIMESTAMP, LOCAL_RUS_DATESTAMP, LOCAL_EASY_DATESTAMP, DATE_STAMP, default_unicode, default_encoding, 
     print_to, print_exception
     )

from .booleval import Token
from .settings import DEFAULT_DATETIME_FORMAT, DEFAULT_DATETIME_INLINE_FORMAT, MAX_LOGS_LEN
from .utils import (
     normpath, getToday, getDate, getDateOnly, checkDate, spent_time, makeSearchQuery, getString, getSQLString,
     Capitalize, unCapitalize, sortedDict, cdate, decoder, pickupKeyInLine
     )

try:
    from types import UnicodeType, StringType
    StringTypes = (UnicodeType, StringType,)
except:
    StringTypes = (str,)

is_v3 = sys.version_info[0] > 2 and True or False

if is_v3:
    from imp import reload

EOL = '\n'
ITEM_DELIMETER_DEFAULT = ':'


##  =======================
##  File-Logger Declaration
##  =======================

class Logger():

    def __init__(self, to_file=None, encoding=default_unicode, mode='w+', bom=True, end_of_line=EOL):
        self.is_to_file = to_file and 1 or 0
        self.encoding = encoding
        self.fo = None
        self.end_of_line = end_of_line

        if IsDisableOutput and to_file:
            pass
        elif to_file:
            if IsLogTrace:
                self.fo = codecs.open(to_file, encoding=self.encoding, mode=mode)
                if bom:
                    self.fo.write(codecs.BOM_UTF8.decode(self.encoding))
                self.out(to_file, console_forced=True)  # _pout('--> %s' % to_file)
        else:
            pass

    def get_to_file(self):
        return self.fo

    def set_default_encoding(self, encoding=default_unicode):
        if sys.getdefaultencoding() == 'ascii':
            reload(sys)
            sys.setdefaultencoding(encoding)
        _pout('--> %s' % sys.getdefaultencoding())

    def out(self, line, console_forced=False, without_decoration=False):
        if not line or not IsLogTrace:
            return
        elif console_forced or not (self.fo or self.is_to_file):
            mask = '%s' % (not without_decoration and '--> ' or '')
            try:
                _pout('%s%s' % (mask, line))
            except:
                if is_v3:
                    pass
                elif type(line) is UnicodeType:
                    v = ''
                    for x in line:
                        try:
                            _pout(x, end='')
                            v += x.encode(default_encoding, 'ignore')
                        except:
                            v += '?'
                    _pout('')
                else:
                    _pout('%s%s' % (mask, line.decode(default_encoding, 'ignore')))
        elif IsDisableOutput:
            return
        else:
            if type(line) in StringTypes:
                try:
                    self.fo.write(line)
                except:
                    if is_v3:
                        return
                    try:
                        self.fo.write(unicode(line, self.encoding))
                    except:
                        try:
                            self.fo.write(line.decode(default_encoding))  # , 'replace'
                        except:
                            raise
                if not line == self.end_of_line:
                    self.fo.write(self.end_of_line)

    def progress(self, line=None, mode='continue'):
        if mode == 'start':
            _pout('--> %s:' % (line or ''), end=' ')
        elif mode == 'end':
            _pout('', end='\n')
        else:
            _pout('#', end='', flush=True)

    def close(self):
        if IsDisableOutput:
            return
        if not self.fo:
            return
        self.fo.close()


ansi = not sys.platform.startswith("posix")

def setup_console(sys_enc=default_unicode):
    """
    Set sys.defaultencoding to `sys_enc` and update stdout/stderr writers to corresponding encoding
    .. note:: For Win32 the OEM console encoding will be used istead of `sys_enc`
    http://habrahabr.ru/post/117236/
    http://www.py-my.ru/post/4bfb3c6a1d41c846bc00009b
    """
    global ansi
    reload(sys)

    try:
        if sys.platform.startswith("win"):
            import ctypes
            enc = "cp%d" % ctypes.windll.kernel32.GetOEMCP()
        else:
            enc = (sys.stdout.encoding if sys.stdout.isatty() else
                   sys.stderr.encoding if sys.stderr.isatty() else
                   sys.getfilesystemencoding() or sys_enc)

        sys.setdefaultencoding(sys_enc)

        if sys.stdout.isatty() and sys.stdout.encoding != enc:
            sys.stdout = codecs.getwriter(enc)(sys.stdout, 'replace')

        if sys.stderr.isatty() and sys.stderr.encoding != enc:
            sys.stderr = codecs.getwriter(enc)(sys.stderr, 'replace')
    except:
        pass

## ---------------------------------------

def getBOM(encoding):
    return codecs.BOM_UTF8.decode(encoding)

def get_opposite_encoding(encoding):
    return encoding == default_encoding and default_unicode or default_encoding


##  ==============================
##  LogGenerator Class Declaration
##  ==============================


def _register_error(errors, e, **kw):
    errors.append({
        'Date' : cdate(getToday(), kw.get('date_format') or UTC_FULL_TIMESTAMP),
        'exception' : str(e),
    })


def is_mask_matched(mask, value):
    return mask and value and re.match(mask, value)

def valid_name(masks, value):
    if not masks:
        return True
    for mask in masks:
        matched = is_mask_matched(mask, value)
        if matched is not None:
            return matched
    return False

def check_path(root, logger):
    for name in os.listdir(root):
        folder = normpath(os.path.join(root, name))

        logger.out('--> %s' % folder)

        if os.path.isdir(folder):
            check_path(folder, logger)

def check_aliases(folder, aliases):
    for alias in aliases:
        if alias.lower() in folder.lower():
            return True
    return False

def walk(config, root, logs, checker=None, **kw):
    files = kw.get('files')
    dates = kw.get('dates')

    obs, n = [], 0

    while n < 3:
        try:
            obs = os.listdir(root)
            break
        except:
            logger.out('... walk error:%s, root:%s' % (n, root))

            time.sleep(3)
            n += 1

    for name in obs:
        folder = normpath(os.path.join(root, name))
        #
        # Check Logs limit
        #
        if logs and len(logs) > MAX_LOGS_LEN:
            break

        if not os.path.exists(folder):
            logger.out('--> walk.not exists folder: %s' % folder)
            continue

        if name in config.get('suspend'):
            logger.out('--> walk.suspended: %s' % name)
            continue
        #
        # Check folder name
        #
        elif os.path.isdir(folder): # and not os.path.islink(folder):
            if not valid_name(config.get('dir'), name):
                logger.out('--> walk.not valid name: %s' % name)
                continue
            if '*' in options:
                pass
            walk(config, folder, logs, checker, **kw)
        #
        # Check file name & start log-checker
        #
        else:
            m = valid_name(config.get('file'), name)
            if not m or not m.groups():
                continue
            filename = normpath(os.path.join(root, name))
            date = m.group(1)

            size = os.path.getsize(filename)

            if size == 0:
                continue

            if files is not None:
                files[filename] = (date, name, size)

            if dates is not None:
                dates.append(date)


## ---------------------------------------

class Base:

    def __init__(self, *args, **kwargs):
        self._started = getToday()
        self.now = getDate(self._started, format=DATE_STAMP)

        if IsDeepDebug:
            print('Base init')

        self.requested_dates = []
        self.date = None

        super().__init__() #*args, **kwargs

        self._page = kwargs.get('page') or 'default'
        self._log_config = kwargs.get('config') or {}

        self._errors = []
        self._files = {}
        self._dates = []

        self._is_error = None
        self.checker = None

    def log_config_item(self, key):
         return self._log_config and self._log_config.get(key) or ''

    def _init_state(self, *args, **kwargs):
        if IsDeepDebug:
            print('Base initstate')

        self.errorlog = self.log_config_item('errorlog') % {'now' : self.now, 'page': self._page}
        self.logger = Logger(self.errorlog)
        self.sort_type = kwargs.get('sort_type') == 'reverse'

        self.root = normpath(os.path.join(basedir, self.log_config_item('root')))

        try:
            walk(self._log_config, self.root, None, self.checker, files=self._files, dates=self._dates)
            self._dates.sort()
            if self.sort_type:
                self._dates.reverse()

        except Exception as e:
            _register_error(self._errors, e, **kwargs)

            if IsPrintExceptions:
                print_exception()

        if IsLogTrace:
            self.logger.out('>>> errors: %s' % self.errors)
            self.logger.out('>>> dates found: %s' % self.dates)
            self.logger.out('>>> files: %s' % self.files)

    @property
    def is_error(self):
        return self.errors and len(self.errors) > 0 and 1 or 0

    @property
    def errors(self):
        return self._errors or None

    @property
    def files(self):
        return self._files or None

    @property
    def files_showname(self):
        return self._files and ['%s: %s [%s]' % x for x in sorted(self._files.values(), key=itemgetter(0), reverse=self.sort_type)] or {}

    @property
    def dates(self):
        return self._dates or []

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except:
            return None

    def get(self, name, default=None):
        v = getattr(self, name)
        if v is None:
            return default
        return v


class LogGenerator(Base):

    def __init__(self, view, *args, **kwargs):
        if IsDeepDebug:
            print('LogGenerator init')

        super().__init__(*args, **kwargs)

        self.view = view
        self.log = None

    def _init_state(self, dates, *args, **kwargs):
        if IsDeepDebug: 
            print('LogGenerator initstate')

        self.requested_dates = dates

        super()._init_state(*args, **kwargs)

        self.item_delimeter = self.log_config_item('delimeter') or ITEM_DELIMETER_DEFAULT

        self.headers = self.view.get('headers')
        self.columns = self.view.get('columns')
        self.export_columns = self.view.get('export')
        self.modes = [(n, '%s' % self.headers[x][0]) for n, x in enumerate(self.export_columns)]

    @property
    def selected_date(self):
        return self.requested_dates == '*' and '*' or self.date

    def is_valid(self):
        return not self.is_error and \
            len(self.headers) == len(self.columns) and len(self.modes) == len(self.export_columns)

    def get_modes(self):
        return self.modes

    def nextdate(self):
        dates = self.requested_dates if '*' not in self.requested_dates else self.dates
        for date in dates:
            yield date

    def open(self):
        try:
            self.file = open(self.log, 'r')
        except:
            self.file = None
            #raise("No file")

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def get_line(self, **kw):
        #
        # status:(value, key, field)
        #
        status = kw.get('status') 
        user = kw.get('user') or None
        search = kw.get('search')

        n = 0
        for date in self.nextdate():
            if not date:
                break

            self.date = date or getDate(getToday(), format=LOCAL_EASY_DATESTAMP)
            self.log = normpath(os.path.join(self.root, '%s_%s.log' % (self.date, self.log_config_item('name'))))

            self.open()
            if self.file is not None and not self.file.closed:
                with self.file as file:
                    for line in file:
                        if not line:
                            break
                        items = line.strip().split(self.item_delimeter)

                        if len(items) != len(self.export_columns):
                            continue

                        row = dict(zip(self.export_columns, items))

                        if status and status[0] and status[1] not in row.get(status[2]):
                            continue
                        if user and isIterable(user) and user[1] and user[1] not in row.get(user[0]):
                            continue
                        if search and search not in line:
                            continue

                        n += 1
                        row['np'] = n

                        yield row

                self.close()


class SpoGenerator(Base):

    def __init__(self, view, *args, **kwargs):
        if IsDeepDebug:
            print('SpoGenerator init')

        super().__init__(*args, **kwargs)

        self.view = view
        self.log = None

    def _init_state(self, dates, *args, **kwargs):
        if IsDeepDebug: 
            print('SpoGenerator initstate')

        super()._init_state(*args, **kwargs)

        self._today = getDate(getToday(), format=LOCAL_EASY_DATESTAMP)
    
        if (not dates or dates[0] == self._today) and not self.is_today_exists:
            self.requested_dates == '*'
        else:
            self.requested_dates = dates

        self.logger.out('>>> requested_dates: %s' % self.requested_dates)

        self.item_delimeter = self.log_config_item('delimeter') or ITEM_DELIMETER_DEFAULT
    
        self.headers = self.view.get('headers')
        self.columns = self.view.get('columns')
        self.export_columns = self.view.get('export')
        self.modes = [(n, '%s' % self.headers[x][0]) for n, x in enumerate(self.export_columns)]

    @property
    def is_today_exists(self):
        return self.dates and self._today in self.dates and 1 or 0
    @property
    def selected_date(self):
        date = self.requested_dates == '*' and '*' or self.date in self.dates and self.date or '*'
        x = getDate(date, format=LOCAL_EASY_DATESTAMP, is_date=True)
        return getDate(x, format=LOCAL_RUS_DATESTAMP) or date

    def is_valid(self):
        return True

    def get_modes(self):
        return self.modes

    def nextdate(self):
        dates = None
        if '*' not in self.requested_dates and self.requested_dates:
            dates = self.requested_dates
        else:
            dates = self.dates
        dates = sorted(dates)
        for date in dates:
            yield date

    def open(self):
        try:
            self.file = open(self.log, 'r')
        except:
            self.file = None
            #raise("No file")

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def get_line(self, **kw):
        #
        # status:(value, key, field)
        #
        status = kw.get('status') 
        user = kw.get('user') or None
        search = kw.get('search')

        n = 0
        for date in self.nextdate():
            if not date:
                break

            self.date = date or getDate(getToday(), format=LOCAL_RUS_DATESTAMP)
            self.log = normpath(os.path.join(self.root, '%s%s.log' % (self.date, self.log_config_item('name'))))

            self.open()
            if self.file is not None and not self.file.closed:
                with self.file as file:
                    for line in file:
                        if not line:
                            break
                        items = line.strip().split(self.item_delimeter)

                        if len(items) != len(self.export_columns):
                            continue

                        row = dict(zip(self.export_columns, items))

                        if status and status[0] and status[1] not in row.get(status[2]):
                            continue
                        if user and isIterable(user) and user[1] and user[1] not in row.get(user[0]):
                            continue
                        if search and search not in line:
                            continue

                        n += 1
                        row['np'] = n

                        yield row

                self.close()

    def row_to_line(self, row):
        line = ''
        for column in self.columns:
            line += str(row.get(column)) or ''
            if column == 'np':
                line += ': '
        return line

    def get_lines(self, **kw):
        #
        # status:(value, key, field)
        #
        status = kw.get('status') 
        user = kw.get('user')
        search = kw.get('search')

        lines = []

        n = 0
        for date in self.nextdate():
            if not date:
                break

            self.date = date or getDate(getToday(), format=LOCAL_RUS_DATESTAMP)
            self.log = normpath(os.path.join(self.root, '%s%s.log' % (self.date, self.log_config_item('name'))))

            print_to(None,'log:%s' % self.log)

            self.open()
            if not self.file is None and not self.file.closed:
                with self.file as file:
                    for line in file:
                        line = file.readline()

                        if line:
                            line = re.sub(r'\n', '<br>', line)

                        lines.append(line)

                self.close()

        return lines
