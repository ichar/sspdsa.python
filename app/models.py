# -*- coding: utf-8 -*-

import os
import sys
import re
from math import ceil
import decimal
from datetime import datetime
from time import time
from collections import namedtuple
from operator import itemgetter
from copy import deepcopy
import requests, json, jwt
from requests.exceptions import ConnectionError, ConnectTimeout

from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin, current_user
from flask_babel import lazy_gettext
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import app_release, db, login_manager

from sqlalchemy import create_engine, MetaData, Sequence
from sqlalchemy import func, asc, desc, and_, or_, text
from sqlalchemy.orm import column_property
from sqlalchemy.event import listen

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, errorlog, 
     default_unicode, default_encoding, default_print_encoding, n_a,
     print_to, print_exception, isIterable,
     UTC_FULL_TIMESTAMP, LOCAL_EASY_DATESTAMP, UTC_EASY_TIMESTAMP,
     connection_params
     )

from .settings import DEFAULT_PER_PAGE, DEFAULT_HTML_SPLITTER, DEFAULT_USER_AVATAR, DEFAULT_UNDEFINED, gettext, g
from .mails import send_simple_mail
from .utils import getDate, getDateOnly, getToday, getTimedelta, out, cid, cdate, clean, image_base64, make_config

roles_ids = ['USER', 'ADMIN', 'EDITOR', 'OPERATOR', 'VISITOR', 'X1', 'X2', 'X3', 'SERVICE', 'ROOT']
roles_names = tuple([lazy_gettext(x) for x in roles_ids])
ROLES = namedtuple('ROLES', ' '.join(roles_ids))
valid_user_roles = [n for n, x in enumerate(roles_ids)]
roles = ROLES._make(zip(valid_user_roles, roles_names))

app_roles_ids = ['EMPLOYEE', 'MANAGER', 'CHIEF', 'ADMIN', 'CTO', 'CAO', 'HEADOFFICE', 'ASSISTANT', 'CEO', 'HOLDER', 'AUDITOR']
app_roles_names = tuple([lazy_gettext(x) for x in app_roles_ids])
APP_ROLES = namedtuple('ROLES', ' '.join(app_roles_ids))
valid_user_app_roles = [n for n, x in enumerate(app_roles_ids)]
app_roles = APP_ROLES._make(zip(valid_user_app_roles, app_roles_names))


APP_SEQUENCES = {
    'ticfg'  : 'ticfg_seq',
    'tsch'   : 'tsch_seq',
    'tuo'    : 'tuo_seq',
    'ttsb'   : 'ttsb_seq',
    'tsb'    : 'tsb_seq',
    'tsd'    : 'tsd_seq',
    'tvsd'   : 'tvsd_seq',
    'tts'    : 'tts_seq',
    'tsnsi'  : 'tsnsi_seq',
    'tvmax'  : 'tvmax_seq',
    'tcepsb' : 'tcepsb_seq',
    'tslsb'  : 'tslsb_seq',
}


USER_DEFAULT_PHOTO = '/static/img/person-default.jpg'

password_mask = '*'*10

admin_config = {
    'users' : {
        'columns' : ('id', 'login', 'name', 'post', 'email', 'role', 'confirmed', 'enabled',),
        'headers' : {
            'id'          : (lazy_gettext('ID'),               '',),
            'login'       : (lazy_gettext('Login'),            '',),
            'name'        : (lazy_gettext('Full person name'), '',),
            'post'        : (lazy_gettext('Post'),             '',),
            'email'       : (lazy_gettext('Email'),            '',),
            'role'        : (lazy_gettext('Role'),             '',),
            'confirmed'   : (lazy_gettext('Confirmed'),        '',),
            'enabled'     : (lazy_gettext('Enabled'),          '',),
        },
        'fields' : ({
            'login'       : lazy_gettext('Login'),
            'password'    : lazy_gettext('Password'),
            'family_name' : lazy_gettext('Family name'),
            'first_name'  : lazy_gettext('First name'),
            'last_name'   : lazy_gettext('Last name'),
            'nick'        : lazy_gettext('Nick'),
            'post'        : lazy_gettext('Post'),
            'email'       : lazy_gettext('Email'),
            'role'        : lazy_gettext('Role'),
            'confirmed'   : lazy_gettext('Confirmed'),
            'enabled'     : lazy_gettext('Enabled'),
        }),
    },
}

UserRecord = namedtuple('UserRecord', admin_config['users']['columns'] + ('selected',))


def _commit(check_session=True, force=None):
    is_error = 0
    errors = []

    if check_session:
        if not (db.session.new or db.session.dirty or db.session.deleted):
            if IsTrace:
                print_to(None, '>>> No data to commit: new[%s], dirty[%s], deleted[%s]' % ( \
                    len(db.session.new),
                    len(db.session.dirty),
                    len(db.session.deleted))
                )
            if not force:
                errors.append('No data to commit')
                is_error = 1

    if not is_error or force:
        try:
            db.session.commit()
            if IsTrace:
                print_to(None, '>>> Commit OK')
        except Exception as error:
            db.session.rollback()
            is_error = 2
            errors.append(error)
            if IsTrace:
                print_to(None, '>>> Commit Error: %s' % error)
            print_to(None, '!!! System Commit Error: %s' % str(error))
            if IsPrintExceptions:
                print_exception()

    return is_error, errors

def _apply_limit(offset, top):
    def wrapped(query):
        if offset:
            query = query.limit(offset)
        if top:
            query = query.offset(top)
        return query
    return wrapped

def _get_offset(query, **kw):
    offset = 0
    top = 0
    page_options = kw.get('page_options')
    if page_options:
        offset = int(page_options.get('offset') or 0)
        top = int(page_options.get('top') or 0)
    return offset, top

def _set_offset(query, **kw):
    page_options = kw.get('page_options')
    offset, top = _get_offset(query, **kw)
    if offset is not None:
        query = query.offset(offset)
    if top is not None:
        query = query.limit(top)

    #listen(query, 'before_compile', _apply_limit(offset, top), retval=True)

    return query

def _set_filter(query, **kw):
    items = []
    args = kw.get('args')
    mode = kw.get('mode')

    if args is not None:
        if IsDebug:
            print_to(None, '\n>>> models._set_filter: %s' % args)

        local_node = args.get('local_node')
        if local_node:
            if mode == 'linestates':
                pass
            elif mode == 'messages':
                query = query.filter(Message.kuo==int(local_node))

        sd, selected_date = None, args.get('selected_date')
        if selected_date and isinstance(selected_date, str):
            sd = getDate(selected_date, format=LOCAL_EASY_DATESTAMP, is_date=True) and selected_date or None
        if sd is not None:
            sd1 = '%s 00:00:00' % sd
            sd2 = '%s 23:59:59' % sd
            if mode == 'linestates':
                #items.append("dtsd >= '%s 00:00:00'" % selected_date)
                #items.append("dtsd <= '%s 23:59:59'" % selected_date)
                query = query.filter(and_(LineState.dtsd >= sd1, LineState.dtsd <= sd2))
            elif mode == 'messages':
                query = query.filter(or_(
                    and_(Message.dtosb >= sd1, Message.dtosb <= sd2),
                    and_(Message.dtpsb >= sd1, Message.dtpsb <= sd2)
                    ))

        selected_line = args.get('selected_line') and args['selected_line'] or None
        if selected_line is not None:
            ksd = node1 = node2 = None
            if isIterable(selected_line) and len(selected_line) == 2:
                node1 = int(selected_line[0])
                node2 = int(selected_line[1])
            else:
                ksd = int(selected_line)
            if mode == 'linestates':
                if ksd:
                    query = query.filter(LineState.ksd==ksd)
            elif mode == 'messages':
                if node1 and node2:
                    query = query.filter(or_(
                        or_(Message.kuoo==node1, Message.kuop==node2),
                        or_(Message.kuoo==node2, Message.kuop==node1)
                        ))

        search = args.get('search') and args['search'] or None
        if search:
            if search.isdigit():
                n = int(search)
                if mode == 'linestates':
                    pass
                elif mode == 'messages':
                    query = query.filter(or_(
                        Message.ns==n,
                        Message.ksb==n,
                        Message.ldata==n
                        ))
            else:
                s = ''.join([x.strip() for x in search.split(' ')]).lower()
                if mode == 'linestates':
                    pass
                elif mode == 'messages':
                    query = query.filter(or_(
                        Message.lgn.match(s), 
                        Node.kikts.match(s),
                        MessageType.itsb.match(s)
                        ))
                    query = query.filter(and_(
                        or_(Message.kuo==Node.kuo,
                            Message.kuoo==Node.kuo,
                            Message.kuop==Node.kuo,
                            Message.kuopr==Node.kuo,
                            Message.kuosl==Node.kuo,
                            ),
                        Message.ktsb == MessageType.ktsb
                        ))

        if IsDeepDebug:
            print_to(None, '>>> models._set_filter.query: \n%s' % query)

        """
        selected_node = args.get('selected_node') or None
        if mode == 'linestates':
            items.append("line.kuo is not null and line.kuov is not null")
            items.append("line.kuo=%s or line.kuo=%s" % (selected_node, selected_node))
        else:
            items.append("line.kuo is not null and line.kuov is not null")

        selected_line = args.get('selected_line') or None
        if selected_line is not None:
            items.append(":scheme:.tvsd.ksd = %s" % selected_line)
        """

    return query

##  ------------
##  Help Classes
##  ------------

class Pagination(object):
    #
    # Simple Pagination
    #
    def __init__(self, page, per_page, total, value, sql):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.value = value
        self.sql = sql

    @property
    def query(self):
        return self.sql

    @property
    def items(self):
        return self.value

    @property
    def current_page(self):
        return self.page

    @property
    def pages(self):
        return int(ceil(self.total / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def get_page_params(self):
        return (self.current_page, self.pages, self.per_page, self.has_prev, self.has_next, self.total,)

    def iter_pages(self, left_edge=1, left_current=0, right_current=3, right_edge=1):
        last = 0
        out = []
        for num in range(1, self.pages + 1):
            if num <= left_edge or (
                num > self.page - left_current - 1 and num < self.page + right_current) or \
                num > self.pages - right_edge:
                if last + 1 != num:
                    out.append(-1)
                out.append(num)
                last = num
        return out

##  ==========================
##  Objects Class Construction
##  ==========================

class ExtClassMethods(object):
    """
        Abstract class methods
    """
    def __init__(self):
        self._is_error = False

    @property
    def is_error(self):
        return self._is_error
    @is_error.setter
    def is_error(self, value):
        self._is_error = value or 0
    
    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def print_all(cls):
        for x in cls.ordered_rows():
            print(x)

    @classmethod
    def next_pk(cls):
        try:
            table = cls.__tablename__
            seq = APP_SEQUENCES.get(table)
            return seq and db.session.execute(Sequence(seq)) or None
        except:
            raise

    @classmethod
    def set_columns(cls, **kw):
        if not kw:
            return
        columns = []
        try:
            columns = list(cls.__table__.columns.keys())
        except:
            pass

        for key in columns:
            if key in kw:
                setattr(cls, key, kw.get(key))

    @staticmethod
    def get_row(np, ob, config, fmt, as_is):
        values = []
        for x in config['original']:
            if x == 'np':
                v = np
            elif type(x) in (int, float) or x is None:
                v = x
            elif 'rel:' in x:
                _, name, key = x.split(':')
                a = getattr(ob, name)
                if a and isIterable(a) and len(a) > 0:
                    v = getattr(a[0], key)
            elif 'date:' in x:
                _, name = x.split(':')
                v = getattr(ob, name)
                if not as_is:
                    v = getDate(v, fmt or UTC_EASY_TIMESTAMP)
            else:
                v = getattr(ob, x)
            if v is None and not as_is:
                v = ''
            values.append(v)
        return values

    @classmethod
    def get_rows(cls, config, id=None, obs=None, as_is=None, **kw):
        """
            Returns table rows in the given config format
            
            Argments:
                config -- dict: database_config item
            
            Keyword arguments:
                id  -- int, return row for the given id only
                obs -- list of objects, source class rows: `ordered_rows` by default
                as-is -- flag, get records as is values: None values, dates and ...
                fmt -- str, datetime format, by default: `UTC_EASY_TIMESTAMP`
                
                Note!
                    If as_is true, don't use datetime format.

            Returns:
                rows -- list of dict, data with column names changed according of column mappings: original -> export
        """
        fmt = kw.get('fmt')
        args = kw.get('args')

        rows = []
        query = None

        offset, top = _get_offset(query, **kw)
        search = (args and args.get('search') or '').lower()

        is_check_search = 0

        if id:
            obs = [cls.get_by_id(id)]
        elif search:
            query = cls.ordered_rows(is_query=True)
            if not is_check_search:
                query = _set_filter(query, **kw)
                query = _set_offset(query, **kw)
            obs = query.all()
        elif obs is None:
            obs = cls.ordered_rows()

        n = 0
        for np, ob in enumerate(obs):
            values = cls.get_row(np, ob, config, fmt, as_is)
            if search and is_check_search:
                context = ':'.join([str(x) for x in values]).lower()
                if search not in context:
                    continue
                if offset and n < offset:
                    continue
                if top and n > top:
                    break
            n += 1
            row = dict(zip(config['export'], values))
            rows.append(row)
        return rows

    @classmethod
    def gen_rows(cls, config, query=None, as_is=None, **kw):
        """
            Returns table rows in the given config format
            
            Argments:
                config -- dict: database_config item
            
            Keyword arguments:
                query -- db query, query for getting source class rows: `ordered_rows(is_query=True)` by default
                as-is -- flag, get records as is values: None values, dates and ...
                fmt -- str, datetime format, by default: `UTC_EASY_TIMESTAMP`
                
                Note!
                    If as_is true, don't use datetime format.

            Returns:
                rows -- list of dict, data with column names changed according of column mappings: original -> export
        """
        fmt = kw.get('fmt')
        args = kw.get('args')

        if query is None:
            query = cls.ordered_rows(is_query=True)
        query = _set_filter(query, **kw)
        query = _set_offset(query, **kw)
        for np, ob in enumerate(query.all()):
            values = cls.get_row(np, ob, config, fmt, as_is)
            row = dict(zip(config['export'], values))
            yield row



class ClientProfile(db.Model, ExtClassMethods):
    """
        Пользовательский профайл (Клиенты-Банки, Клиентский сегмент)
    """
    __tablename__ = 'client_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ClientID = db.Column(db.Integer, index=True, nullable=False, default=0)

    user = db.relationship('User', backref=db.backref('clients', lazy='joined'), uselist=True) #, lazy='dynamic'

    def __init__(self, user, client_id):
        self.user_id = user.id
        self.ClientID = client_id

    def __repr__(self):
        return '<ClientProfile %s:[%s-%s]>' % (cid(self), str(self.user_id), str(self.ClientID))


class Photo(db.Model, ExtClassMethods):
    """
        Пользовательский профайл (Фото)
    """
    __tablename__ = 'photo'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    data = db.Column(db.Text, nullable=True, default=None)

    user = db.relationship('User', backref=db.backref('photos', lazy='joined'), uselist=True) #, lazy='dynamic'

    def __init__(self, user, data):
        self.user_id = user.id
        self.data = data

    def __repr__(self):
        return '<Photo %s:[%s-%s]>' % (cid(self), str(self.user_id), self.data and 'Y' or 'N')


class Settings(db.Model, ExtClassMethods):
    """
        Пользовательский профайл (настройки интерфейса)
    """
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    pagesize_bankperso = db.Column(db.Integer, nullable=True)
    pagesize_cards = db.Column(db.Integer, nullable=True)
    pagesize_persostation = db.Column(db.Integer, nullable=True)
    pagesize_config = db.Column(db.Integer, nullable=True)
    pagesize_provision = db.Column(db.Integer, nullable=True)

    sidebar_collapse = db.Column(db.Boolean, default=True)
    use_extra_infopanel = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('settings', lazy='joined'), uselist=True) #, lazy='dynamic'

    def __init__(self, user):
        self.user_id = user.id

    def __repr__(self):
        return '<Settings %s:[%s-%s]>' % (cid(self), str(self.user_id), self.user_id and 'Y' or 'N')


class Subdivision(db.Model, ExtClassMethods):
    """
        Подразделения организации
    """
    __tablename__ = 'subdivisions'

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(20), index=True)
    name = db.Column(db.Unicode(50), default='')
    manager = db.Column(db.Unicode(50), default='')
    fullname = db.Column(db.Unicode(200), default='')
    
    def __init__(self, code, name, manager=None, fullname=None):
        self.code = code
        self.name = name
        self.manager = manager
        self.fullname = fullname

    def __repr__(self):
        return '<Subdivision %s:[%s-%s]>' % (cid(self), str(self.code), self.name)

    @classmethod
    def get_by_code(cls, code):
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_manager(cls, id):
        return cls.query.filter_by(id=id).first().manager


class Privileges(db.Model, ExtClassMethods):
    """
        Привилегии пользователей
    """
    __tablename__ = 'privileges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subdivision_id = db.Column(db.Integer, db.ForeignKey('subdivisions.id'))

    menu = db.Column(db.String(50), default='')
    base_url = db.Column(db.String(120), index=True)
    role = db.Column(db.SmallInteger, default=app_roles.EMPLOYEE[0])

    is_manager = db.Column(db.Boolean, default=False)
    is_author = db.Column(db.Boolean, default=False)
    is_consultant = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('privileges', lazy='joined'), uselist=True) #, lazy='dynamic'
    subdivision = db.relationship('Subdivision', backref=db.backref('privileges', lazy='joined'), uselist=True) #, lazy='dynamic'

    def __init__(self, user, subdivision):
        self.user_id = user.id
        self.subdivision_id = subdivision and subdivision.id or None

    def __repr__(self):
        return '<Privileges %s:[%s-%s] [%s] [%s] %s>' % (
            cid(self), 
            str(self.user_id), 
            str(self.subdivision_id), 
            self.app_role_name,
            '%s|%s' % (self.subdivision_name, self.subdivision_code),
            self.user[0].login
            )

    @property
    def app_role_name(self):
        return self.role in valid_user_app_roles and app_roles_names[self.role] or gettext('undefined')

    @property
    def subdivision_name(self):
        return self.subdivision and self.subdivision[0].name or ''

    @property
    def subdivision_fullname(self):
        return self.subdivision and self.subdivision[0].fullname or ''

    @property
    def subdivision_code(self):
        return self.subdivision and self.subdivision[0].code or ''


class User(UserMixin, db.Model, ExtClassMethods):
    """
        Пользователи
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    reg_date = db.Column(db.DateTime, index=True)

    login = db.Column(db.Unicode(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    nick = db.Column(db.Unicode(40), default='')
    first_name = db.Column(db.Unicode(50), default='')
    family_name = db.Column(db.Unicode(50), default='')
    last_name = db.Column(db.Unicode(50), default='')
    role = db.Column(db.SmallInteger, default=roles.USER[0])
    email = db.Column(db.String(120), index=True)

    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    last_visit = db.Column(db.DateTime)
    last_pwd_changed = db.Column(db.DateTime)

    confirmed = db.Column(db.Boolean, default=False)
    enabled = db.Column(db.Boolean, default=True)

    post = db.Column(db.String(100), default='')

    def __init__(self, login, name=None, role=None, email=None, **kw):
        super(User, self).__init__(**kw)
        self.login = login
        self.set_name(name, **kw)
        self.role = role and role in valid_user_roles and role or roles.USER[0]
        self.post = kw.get('post') or ''
        self.email = not email and '' or email
        self.reg_date = datetime.now()

    def __repr__(self):
        return '<User %s:%s %s>' % (cid(self), str(self.login), self.full_name())

    @classmethod
    def get_by_login(cls, login):
        return cls.query.filter_by(login=login).first()

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_login(login):
        return User.query.filter_by(login=login).first()

    def has_privileges(self):
        return self.privileges is not None and len(self.privileges) > 0 and True or False

    @property
    def app_menu(self):
        return self.has_privileges() and self.privileges[0].menu or 'default'
    @property
    def base_url(self):
        return self.has_privileges() and self.privileges[0].base_url or ''
    @property
    def role_name(self):
        return self.role in valid_user_roles and roles_names[self.role] or gettext('undefined')
    @property
    def subdivision(self):
        return self.has_privileges() and self.privileges[0].subdivision_id or 0
    @property
    def subdivision_code(self):
        return self.has_privileges() and self.privileges[0].subdivision_code or None
    @property
    def subdivision_fullname(self):
        return self.has_privileges() and self.privileges[0].subdivision_fullname or None
    @property
    def subdivision_id(self):
        return self.has_privileges() and self.privileges[0].subdivision_id or None
    @property
    def subdivision_name(self):
        return self.has_privileges() and self.privileges[0].subdivision_name or None
    
    #   --------------
    #   Authentication
    #   --------------
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def change_password(self, password):
        self.password = password
        self.confirmed = True
        self.last_pwd_changed = datetime.now()
        db.session.add(self)

    def unconfirmed(self):
        self.confirmed = False
        db.session.add(self)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def get_reset_password_token(self, expires_in=600):
        payload = {'reset_password': self.id, 'exp': time() + expires_in}
        key = current_app.config['SECRET_KEY']
        x = jwt.encode(payload, key, algorithm='HS256')
        return type(x) == str and x or x.decode(default_unicode)

    @staticmethod
    def verify_reset_password_token(token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            id = data['reset_password']
        except:
            if IsPrintExceptions:
                print_exception()
            return
        return User.query.get(id)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode(default_unicode)

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        _commit(True)

    #   -------------------------
    #   Basic roles & permissions
    #   -------------------------

    def can(self, role):
        return self.role is not None and roles[self.role] == role

    def is_superuser(self, private=False):
        return self.role in (roles.ROOT[0],)

    def is_administrator(self, private=False):
        if private:
            return self.role == roles.ADMIN[0]
        return self.role in (roles.ADMIN[0], roles.ROOT[0])

    def is_manager(self, private=False):
        if private:
            return self.role == roles.EDITOR[0]
        return self.role in (roles.EDITOR[0], roles.ADMIN[0], roles.ROOT[0])

    def is_operator(self, private=False):
        if private:
            return self.role == roles.OPERATOR[0]
        return self.role in (roles.OPERATOR[0], roles.ADMIN[0], roles.ROOT[0])

    def is_owner(self):
        return self.login == 'admin'

    def is_any(self):
        return self.enabled and True or False

    def is_anybody(self):
        return self.is_any()

    def is_nobody(self):
        return False

    @property
    def is_user(self):
        return self.role in (roles.USER[0], roles.OPERATOR[0], roles.EDITOR[0], roles.ADMIN[0], roles.ROOT[0])

    @property
    def is_emailed(self):
        return self.enabled and self.email and (
            not g.system_config.EXCLUDE_EMAILS or self.email not in g.system_config.EXCLUDE_EMAILS) and True or False

    def get_profile_clients(self, by_list=None):
        items = []
        for ob in self.clients:
            items.append(str(ob.ClientID))
        if by_list:
            return items
        return DEFAULT_HTML_SPLITTER.join(items)

    def set_profile_clients(self, data):
        is_changed = False
        for ob in self.clients:
            db.session.delete(ob)
            is_changed = True
        for id in data.split(':'):
            if not id:
                continue
            try:
                item = ClientProfile(self, int(id))
                db.session.add(item)
                is_changed = True
            except ValueError:
                pass
        if is_changed:
            _commit(True)

    def get_post(self):
        return re.sub(r'"', '&quot;', self.post)

    def get_user_post(self):
        return '%s, %s' % (self.subdivision_name, re.sub(r'"', '&quot;', self.post))

    def get_avatar(self):
        return self.photos and DEFAULT_USER_AVATAR[0] % (self.photos[0].data, self.get_user_post(), self.login) or ''

    def get_small_avatar(self, **kw):
        photo = self.photos and self.photos[0].data or None
        if not photo:
            return ''
        tag, default_image, x, image_type, size = DEFAULT_USER_AVATAR
        try:
            photo = image_base64('', image_type, kw.get('size') or size, photo)
        except:
            return ''
        if kw.get('clean'):
            return photo
        return tag % (photo, self.get_user_post(), self.login)

    def get_photo(self):
        return self.photos and self.photos[0].data or USER_DEFAULT_PHOTO

    def set_photo(self, data):
        is_changed = False
        for ob in self.photos:
            db.session.delete(ob)
            is_changed = True
        try:
            item = Photo(self, data)
            db.session.add(item)
            is_changed = True
        except ValueError:
            pass
        if is_changed:
            _commit(True)

    def delete_photo(self):
        is_changed = False
        for ob in self.photos:
            db.session.delete(ob)
            is_changed = True
        if is_changed:
            _commit(True)
        return self.get_photo()

    def get_pagesize(self, model):
        if not model or model == 'bankperso':
            return self.pagesize_bankperso
        elif model == 'cards':
            return self.pagesize_cards
        elif model == 'persostation':
            return self.pagesize_persostation
        elif model in 'config:configurator':
            return self.pagesize_config
        elif model == 'provision':
            return self.pagesize_provision
        return None

    def set_pagesize(self, model, value):
        is_changed = False
        if not self.has_settings():
            settings = self.add_settings()
            is_changed = True
        else:
            settings = self.settings[0]
        if not model or model == 'bankperso':
            settings.pagesize_bankperso = value
            is_changed = True
        elif model == 'cards':
            settings.pagesize_cards = value
            is_changed = True
        elif model == 'persostation':
            settings.pagesize_persostation = value
            is_changed = True
        elif model in 'config:configurator':
            settings.pagesize_config = value
            is_changed = True
        elif model == 'provision':
            settings.pagesize_provision = value
            is_changed = True
        if is_changed:
            _commit(True)

    def has_settings(self):
        return self.settings and len(self.settings) > 0

    @property
    def pagesize_bankperso(self):
        return self.has_settings() and self.settings[0].pagesize_bankperso or 10
    @property
    def pagesize_cards(self):
        return self.has_settings() and self.settings[0].pagesize_cards or 20
    @property
    def pagesize_persostation(self):
        return self.has_settings() and self.settings[0].pagesize_persostation or 10
    @property
    def pagesize_config(self):
        return self.has_settings() and self.settings[0].pagesize_config or 10
    @property
    def pagesize_provision(self):
        return self.has_settings() and self.settings[0].pagesize_provision or 10
    @property
    def sidebar_collapse(self):
        if self.has_settings():
            return self.settings[0].sidebar_collapse or False
        else:
            return False

    @sidebar_collapse.setter
    def sidebar_collapse(self, collapse):
        is_changed = False
        if not self.has_settings():
            settings = self.add_settings()
            is_changed = True
        else:
            settings = self.settings[0]
        if settings.sidebar_collapse != collapse:
            settings.sidebar_collapse = collapse and True or False
            is_changed = True
        if is_changed:
            _commit(True)

    @property
    def use_extra_infopanel(self):
        if self.has_settings():
            return self.has_settings() and self.settings[0].use_extra_infopanel or False
        else:
            return False

    @staticmethod
    def get_role(role):
        for x in roles:
            if x[0] == role:
                return x
        return None

    @staticmethod
    def get_roles(ids=None):
        try:
            return [getattr(roles, x) for x in vars(roles) if not ids or x in ids]
        except:
            return [getattr(roles, x) for x in roles._fields if not ids or x in ids]

    def get_settings(self):
        return [self.pagesize_bankperso, 
                self.pagesize_cards, 
                self.pagesize_persostation, 
                self.pagesize_config, 
                self.pagesize_provision, 
                self.sidebar_collapse, 
                self.use_extra_infopanel
            ]

    def add_settings(self):
        settings = Settings(self)
        db.session.add(settings)
        return settings

    def set_settings(self, values):
        if not values:
            return
        check_session = True
        is_changed = False
        is_add = False
        try:
            if not self.settings:
                settings = Settings(self)
                is_add = True
            else:
                settings = self.settings[0]
            settings.pagesize_bankperso = int(values[0])
            settings.pagesize_cards = int(values[1])
            settings.pagesize_persostation = int(values[2])
            settings.pagesize_config = int(values[3])
            settings.pagesize_provision = int(values[4])
            settings.sidebar_collapse = values[5] == '1' and True or False
            settings.use_extra_infopanel = values[6] == '1' and True or False
            if is_add:
                db.session.add(settings)
            else:
                self.settings[0] = settings
                check_session = False
            is_changed = True
        except ValueError:
            pass
        if is_changed:
            _commit(check_session)

    def get_privileges(self):
        return [self.subdivision, 
                self.app_role, 
                self.app_menu, 
                self.base_url, 
                self.app_is_manager, 
                self.app_is_author,
                self.app_is_consultant,
            ]

    def set_privileges(self, values):
        if not values:
            return
        check_session = True
        is_changed = False
        is_add = False
        try:
            subdivision_id = int(values[0])
            subdivision = Subdivision.get_by_id(subdivision_id)
            if not self.privileges:
                privileges = Privileges(self, subdivision)
                is_add = True
            else:
                privileges = self.privileges[0]
                if privileges.subdivision_id != subdivision_id:
                    privileges.subdivision_id = subdivision_id
            privileges.role = int(values[1])
            privileges.menu = values[2]
            privileges.base_url = values[3]
            privileges.is_manager = values[4] == '1' and True or False
            privileges.is_author = values[5] == '1' and True or False
            privileges.is_consultant = values[6] == '1' and True or False
            if is_add:
                db.session.add(privileges)
            else:
                self.privileges[0] = privileges
                check_session = False
            is_changed = True
        except ValueError:
            pass
        if is_changed:
            _commit(check_session)

    def full_name(self):
        return ('%s %s %s' % (self.family_name, self.first_name, self.last_name)).strip()

    def short_name(self, is_back=None):
        if self.family_name and self.first_name and self.last_name:
            f = self.family_name
            n = self.first_name and '%s.' % self.first_name[0] or ''
            o = self.last_name and '%s.' % self.last_name[0] or ''
            return (is_back and 
                '%s%s %s' % (n, o, f) or 
                '%s %s%s' % (f, n, o)
                ).strip()
        return self.full_name()

    def set_name(self, name=None, **kw):
        if name and isIterable(name):
            self.first_name = name[0] or ''
            self.last_name = len(name) > 1 and name[1] or ''
            self.family_name = len(name) > 2 and name[2] or ''
        self.nick = kw.get('nick') or ''

    def get_data(self, mode=None, **kw):
        if not mode or mode == 'view':
            data = { 
                'id'          : self.id,
                'login'       : self.login,
                'name'        : self.full_name(),
                'post'        : self.post,
                'email'       : self.email,
                'role'        : User.get_role(self.role)[1],
                'confirmed'   : self.confirmed and 'Да' or 'Нет',
                'enabled'     : self.enabled and 'Да' or 'Нет',
                'selected'    : kw.get('id') == self.id and 'selected' or '',
            }
        elif mode == 'register':
            data = { 
                'id'          : self.id,
                'login'       : self.login,
                'password'    : self.password_hash and password_mask or '',
                'family_name' : self.family_name,
                'first_name'  : self.first_name,
                'last_name'   : self.last_name,
                'post'        : self.post,
                'email'       : self.email,
                'role'        : self.role,
                'confirmed'   : self.confirmed,
                'enabled'     : self.enabled,
            }
        else:
            data = {}
        
        return data

    #   -------------------------------
    #   Application roles & permissions
    #   -------------------------------

    @property
    def app_is_manager(self):
        # Роль: Менеджер
        return self.has_privileges() and self.privileges[0].is_manager or False
    @property
    def app_is_consultant(self):
        # Роль: Консультант
        return self.has_privileges() and self.privileges[0].is_consultant or False
    @property
    def app_is_author(self):
        # Роль: Автор
        return self.has_privileges() and self.privileges[0].is_author or False
    @property
    def app_role(self):
        return self.has_privileges() and self.privileges[0].role or 0
    @property
    def app_role_name(self):
        role = self.app_role
        return role in valid_user_app_roles and app_roles_names[role] or ''


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self, private=False):
        return False

    @property
    def is_emailed(self):
        return False

login_manager.anonymous_user = AnonymousUser


## ==================================================== ##


##  -----------------------------
##  Sequencies defined explicitly
##  -----------------------------

ConfigChange_seq = Sequence(APP_SEQUENCES['ticfg'])  
Division_seq = Sequence(APP_SEQUENCES['tsch'])
Node_seq = Sequence(APP_SEQUENCES['tuo'])
MessageType_seq = Sequence(APP_SEQUENCES['ttsb'])
Line_seq = Sequence(APP_SEQUENCES['tsd'])
LineState_seq = Sequence(APP_SEQUENCES['tvsd'])
Message_seq = Sequence(APP_SEQUENCES['tsb'])
Equipment_seq = Sequence(APP_SEQUENCES['tts'])
Bind_seq = Sequence(APP_SEQUENCES['tsnsi'])
Speed_seq = Sequence(APP_SEQUENCES['tvmax'])
Chain_seq = Sequence(APP_SEQUENCES['tcepsb'])
Signal_seq = Sequence(APP_SEQUENCES['tslsb'])

##  ======================
##  Application Data Model
##  ======================


class ConfigChange(db.Model, ExtClassMethods):
    """
        1. Таблица. Изменения конфигуратора СПО
    """
    __tablename__ = 'ticfg'

    # 1. CONFIG CHANGES ITEM ID 
    kicfg = db.Column(db.BigInteger, primary_key=True)
    #kicfg = db.Column(db.Integer, ConfigChange_seq, primary_key=True, server_default=ConfigChange_seq.next_value())
    # 2. LOGIN
    lgn = db.Column(db.String(40), index=True)
    # 3. TIMESTAMP
    dticfg = db.Column(db.DateTime)
    # 4. BEFORE
    fragd = db.Column(db.Text, nullable=True, default=None)
    # 4. AFTER
    fragp = db.Column(db.Text, nullable=True, default=None)

    def __init__(self, user, **kw):
        super(ConfigChange, self).__init__(**kw)
        self.lgn = user.login
        self.dticfg = datetime.now()

    def __repr__(self):
        return '<ConfigChange %s:[%s, %s] before:[%s] after:[%s]>' % (
            self.kicfg and str(self.kicfg) or n_a, 
            str(self.lgn), 
            getDate(self.dticfg, UTC_FULL_TIMESTAMP),
            len(self.fragd),
            len(self.fragp),
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kicfg=id).first()
    @staticmethod
    def get_changes_by_login(login):
        return ConfigChange.query.filter_by(lgn=login).all()
    @staticmethod
    def get_changes_by_timestamp(timestamp):
        return ConfigChange.query.filter_by(dticfg=getDate(timestamp, UTC_EASY_TIMESTAMP)).all()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.dticfg).order_by(cls.lgn)
        if is_query:
            return query
        return query.all()


class Division(db.Model, ExtClassMethods):
    """
        2. Справочник. Составные части НСК
    """
    __tablename__ = 'tsch'

    # 1. DIVISION ID
    #nsch = db.Column(db.BigInteger, primary_key=True)
    nsch = db.Column(db.BigInteger, Division_seq, primary_key=True, server_default=Division_seq.next_value())
    # 2. NAME
    isch = db.Column(db.Unicode(30))
    # 3. NCH
    vch = db.Column(db.Unicode(10))

    def __init__(self, pk=None, **kw):
        super(Division, self).__init__(**kw)
        if pk is None:
            return
        self.nsch = pk

    def __repr__(self):
        return '<Division %s: isch:[%s] vch:[%s]>' % (
            self.nsch and str(self.nsch) or n_a, 
            str(self.isch), 
            str(self.vch), 
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(nsch=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.nsch)
        if is_query:
            return query
        return query.all()
        
    @classmethod
    def divisions(cls):
        return db.session.query(cls.nsch, cls.isch, cls.vch).order_by(cls.nsch).all()


class MessageType(db.Model, ExtClassMethods):
    """
        3. Справочник. Типы сообщений
    """
    __tablename__ = 'ttsb'

    # 1. MESSATETYPE ID
    #ktsb = db.Column(db.Integer, primary_key=True)
    ktsb = db.Column(db.BigInteger, MessageType_seq, primary_key=True, server_default=MessageType_seq.next_value())
    # 2. NAME
    itsb = db.Column(db.Unicode(256))
    # 3. PRIORITY
    prior = db.Column(db.SmallInteger)

    def __init__(self, pk=None, **kw):
        super(MessageType, self).__init__(**kw)
        if pk is not None:
            self.ktsb = pk

    def __repr__(self):
        return '<Message[%s] pk:%s %s prior:[%s]>' % (
            self.__tablename__,
            self.ktsb and str(self.ktsb) or n_a,
            self.itsb,
            self.prior,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(ktsb=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.ktsb)
        if is_query:
            return query
        return query.all()


class Equipment(db.Model, ExtClassMethods):
    """
        4. Справочник. Технические средства
    """
    __tablename__ = 'tts'

    # 1. EQUIPMENT ID
    #kts = db.Column(db.Integer, primary_key=True)
    kts = db.Column(db.BigInteger, Equipment_seq, primary_key=True, server_default=Equipment_seq.next_value())
    # 2. NAME
    its = db.Column(db.String(256))
    # 3. IP-ADDR
    ip = db.Column(db.String(15))
    # 4. STATE
    sts = db.Column(db.SmallInteger())

    def __init__(self, pk=None, **kw):
        super(Equipment, self).__init__(**kw)
        if pk is not None:
            self.kts = pk

    def __repr__(self):
        return '<Equipment[%s] pk:%s %s ip:[%s] state:[%s]>' % (
            self.__tablename__,
            self.kts and str(self.kts) or n_a, 
            self.its,
            self.ip,
            self.sts,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kts=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.kts).order_by(cls.ip)
        if is_query:
            return query
        return query.all()


class Node(db.Model, ExtClassMethods):
    """
        5. Таблица. Узлы обмена
    """
    __tablename__ = 'tuo'

    # 1. NODE ID
    #kuo = db.Column(db.Integer, primary_key=True)
    kuo = db.Column(db.BigInteger, Node_seq, primary_key=True, server_default=Node_seq.next_value())
    # 2. DIVISION ID (FK)
    nsch = db.Column(db.BigInteger, db.ForeignKey('tsch.nsch'))
    # 3. EQUIPMENT NUMBER
    #nkts = db.Column(db.BigInteger, db.ForeignKey('tts.kts'), index=True)
    nkts = db.Column(db.Integer)
    # 4. IP-ADDR
    ip = db.Column(db.String(15), index=True)
    # 5. STATE 0|1|2
    suo = db.Column(db.Numeric(1))
    # 6. NAME
    kikts = db.Column(db.Unicode(20))
    # 7. LEVEL 1|2|3
    uruo = db.Column(db.Numeric(1))
    # 8. TIMESTAMP
    dtuo = db.Column(db.DateTime)
    # 8. FULLNAME
    pikts = db.Column(db.Unicode(256))
    # 9. PORTS RANGE--1
    port1 = db.Column(db.Integer)
    # 10.PORTS RANGE--2
    port2 = db.Column(db.Integer)

    division = db.relationship('Division', backref=db.backref('tuo', lazy='joined'), uselist=True) #, lazy='dynamic'
    #equipment = db.relationship('Equipment', backref=db.backref('tuo', lazy='joined'), uselist=True)

    def __init__(self, pk=None, nsch=None, nkts=None, **kw):
        super(Node, self).__init__(**kw)
        if pk is not None:
            self.kuo = pk
        if nsch is not None:
            self.nsch = nsch
        if nkts is not None:
            self.nkts = nkts

    def __repr__(self):
        columns = self.__table__.columns.keys()
        return '<Node[%s] pk:%s %s(%s) nsch:%s nkts:%s %s uruo:%s suo:[%s] %s>' % (
            self.__tablename__,
            self.kuo and str(self.kuo) or n_a, 
            self.kikts, self.pikts, 
            self.nsch, 
            self.nkts, 
            'ip' in columns and 'ip:[%s] ports:[%s-%s]' % (self.ip, self.port1, self.port2) or '',
            self.uruo,
            self.suo,
            getDate(self.dtuo, UTC_EASY_TIMESTAMP),
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kuo=id).first()
    @property
    def get_division(cls):
        return cls.division
    @property
    def get_equipment(cls):
        return cls.equipment
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query =  query.order_by(cls.uruo).order_by(cls.nsch).order_by(cls.nkts)
        if is_query:
            return query
        return query.all()
    @classmethod
    def nodes(cls):
        return db.session.query(cls) \
            .order_by(cls.uruo) \
            .order_by(cls.nsch) \
            .order_by(cls.nkts) \
            .all()
    @classmethod
    def get_local_node(cls, local_node):
        nsch, nkts = local_node
        return db.session.query(cls) \
            .filter_by(nsch=nsch) \
            .filter_by(nkts=nkts) \
            .first()


class Line(db.Model, ExtClassMethods):

    """
        6. Таблица. Соединения (2 foreign keys for Node !!!)
    """
    __tablename__ = 'tsd'

    # 1. LINE ID
    #ksd = db.Column(db.Integer, primary_key=True)
    ksd = db.Column(db.BigInteger, Line_seq, primary_key=True, server_default=Line_seq.next_value())
    # 2. NODE ID
    kuo = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 3. NODE-TOP ID
    kuov = db.Column(db.Integer, db.ForeignKey('tuo.kuo'), index=True)
    # 4. STATE: 0|1
    ssd = db.Column(db.SmallInteger)

    node1 = db.relationship('Node', backref=db.backref('line1', lazy='joined'), uselist=True, foreign_keys=kuo)
    node2 = db.relationship('Node', backref=db.backref('line2', lazy='joined'), uselist=True, foreign_keys=kuov)

    def __init__(self, pk=None, kuo=None, kuov=None, **kw):
        super(Line, self).__init__(**kw)
        if pk is not None:
            self.ksd = pk
        if kuo is not None:
            self.kuo = kuo
        if kuov is not None:
            self.kuov = kuov

    def __repr__(self):
        return '<Line[%s] pk:%s [%s-%s] state:[%s]>' % (
            self.__tablename__,
            self.ksd and str(self.ksd) or n_a, 
            self.kuo, self.kuov,
            self.ssd,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(ksd=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session
        query = _set_filter(query, **kw)
        query = query.query(cls).order_by(cls.ksd)
        if is_query:
            return query
        return query.all()
    @classmethod
    def lines(cls, node=None, is_query=None):
        query = db.session.query(cls)
        if node:
            query = query.filter(or_(cls.kuo==node, cls.kuov==node))
        query = query.order_by(cls.kuo).order_by(cls.kuov)
        if is_query:
            return query
        return query.all()


class LineState(db.Model, ExtClassMethods):
    """
        7. Таблица. Включения соединений
    """
    __tablename__ = 'tvsd'

    # 1. LINE STATE ID
    #kvsd = db.Column(db.Integer, primary_key=True)
    kvsd = db.Column(db.BigInteger, LineState_seq, primary_key=True, server_default=LineState_seq.next_value())
    # 2. LINE ID
    ksd = db.Column(db.BigInteger, db.ForeignKey('tsd.ksd'), index=True)
    # 3. TIMESTAMP STATE
    dtsd = db.Column(db.TIMESTAMP)
    # 4. LINE STATE 1|0
    prvsd = db.Column(db.Numeric(1))

    line = db.relationship('Line', backref=db.backref('linestate', lazy='dynamic'), uselist=True, foreign_keys=ksd) #, lazy='joined'

    def __init__(self, pk=None, ksd=None, **kw):
        super(LineState, self).__init__(**kw)
        if pk is not None:
            self.kvsd = pk
        if ksd is not None:
            self.ksd = ksd

    def __repr__(self):
        return '<LineState[%s] pk:%s line:[%s] time:[%s] state:[%s]>' % (
            self.__tablename__,
            self.kvsd and str(self.kvsd) or n_a, 
            self.ksd,
            getDate(self.dtsd, UTC_EASY_TIMESTAMP),
            self.prvsd,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kvsd=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(desc(cls.dtsd)).order_by(cls.ksd)
        if is_query:
            return query
        return query.all()
    @classmethod
    def states(cls, is_query=None):
        query = db.session.query(cls, Line, Node) \
            .join(Line, cls.ksd == Line.ksd) \
            .join(Node, Line.kuo == Node.kuo)
        if is_query:
            return query
        return query.all()


class Message(db.Model, ExtClassMethods):
    """
        8. Таблица. Сообщения (2 foreign keys for Node !!!)
    """
    __tablename__ = 'tsb'

    # 1. MESSAGE ID
    ksb = db.Column(db.BigInteger, Message_seq, primary_key=True, server_default=Message_seq.next_value())
    # 2.  NODE (FK)
    kuo = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 3. SENDER (FROM, FK)
    kuoo = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 4. MESSAGE NUMBER
    ns = db.Column(db.Integer)
    # 5. SENDER LOGIN 
    lgn = db.Column(db.Unicode(40))
    # 6. RECEIVER (TO, FK)
    kuop = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 7. MESSAGETYPE (FK)
    ktsb = db.Column(db.BigInteger, db.ForeignKey('ttsb.ktsb'), index=True)
    # 8. LENGTH
    ldata = db.Column(db.Integer)
    # 9. BEFORE(FK)
    kuopr = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 10. RECEIVED
    dtpsb = db.Column(db.TIMESTAMP)
    # 11. RECEIPT-1
    kvt1 = db.Column(db.Numeric(1))
    # 12. SENT
    dtokvt1 = db.Column(db.TIMESTAMP)
    # 13. NEXT(FK)
    kuosl = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 14. SENDING NEXT
    dtosb = db.Column(db.TIMESTAMP)
    # 15. RECEIPT-2
    kvt2 = db.Column(db.Numeric(1))
    # 16. RECEIPT-2 RECEIVED
    dtpkvt2 = db.Column(db.TIMESTAMP)

    node = db.relationship('Node', backref=db.backref('mou1', lazy='dynamic'), uselist=True, foreign_keys=[kuo])
    sender = db.relationship('Node', backref=db.backref('muo2', lazy='dynamic'), uselist=True, foreign_keys=[kuoo])
    receiver = db.relationship('Node', backref=db.backref('muo3', lazy='dynamic'), uselist=True, foreign_keys=[kuop])
    before = db.relationship('Node', backref=db.backref('muo4', lazy='dynamic'), uselist=True, foreign_keys=[kuopr])
    after = db.relationship('Node', backref=db.backref('muo5', lazy='dynamic'), uselist=True, foreign_keys=[kuosl])
    messagetype = db.relationship('MessageType', backref=db.backref('tsb', lazy='dynamic'), uselist=True)

    def __init__(self, pk=None, kuoo=None, kuop=None, ktsb=None, **kw):
        super(Message, self).__init__(**kw)
        if pk is not None:
            self.ksb = pk
        if kuoo is not None:
            self.kuoo = kuoo
        if kuop is not None:
            self.kuop = kuop
        if ktsb is not None:
            self.ktsb = ktsb

    def __repr__(self):
        columns = self.__table__.columns.keys()
        return '<Message[%s] pk:%s ns:[%s] type:[%s] size:%s login:%s route:[%s-%s-%s-%s] sent:[%s] received:[%s] kvt:[%s-%s] dtkvt:[%s-%s]>' % (
            self.__tablename__,
            self.ksb and str(self.ksb) or n_a, 
            self.ns,
            self.ktsb,
            self.ldata,
            self.lgn,
            self.kuoo, self.kuop, self.kuopr, self.kuosl, 
            getDate(self.dtosb, UTC_EASY_TIMESTAMP),
            getDate(self.dtpsb, UTC_EASY_TIMESTAMP),
            self.kvt1, self.kvt2, 
            getDate(self.dtokvt1, UTC_EASY_TIMESTAMP),
            getDate(self.dtpkvt2, UTC_EASY_TIMESTAMP),
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(ksb=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.ksb)
        if is_query:
            return query
        else:
            return query.all()
    @classmethod
    def messages(cls, is_query=None):
        query = db.session.query(cls, Node, MessageType) \
            .join(Node, cls.kuo == Node.kuo) \
            .join(MessageType, cls.ktsb == MessageType.ktsb)
        if is_query:
            return query
        return query.all()


class Bind(db.Model, ExtClassMethods):
    """
        9. Таблица. Синхронизация НСИ (no primary key!!!)
    """
    __tablename__ = 'tsnsi'

    # 1. DIVISION ID
    nsch = db.Column(db.BigInteger, primary_key=True)
    # 2. DATETIME OF UPDATING
    dtizm = db.Column(db.TIMESTAMP)
    # 3. DATETIME OF SENDING
    dtnsi = db.Column(db.TIMESTAMP)
    # 4. RECEIPT
    kvt = db.Column(db.Numeric(1))
    # 4. DATETIME OF RECEIPT
    dtkvt = db.Column(db.TIMESTAMP)

    division = db.relationship('Division', backref=db.backref('tsnsi', lazy='joined'),
        primaryjoin=nsch == Division.nsch, foreign_keys=nsch, viewonly=True, sync_backref=False,
        uselist=True) #, lazy='dynamic'

    def __init__(self, pk=None, **kw):
        super(Bind, self).__init__(**kw)
        if pk is not None:
            self.nsch = pk

    def __repr__(self):
        return '<Bind[%s] pk:%s: state:[%s] dtizm:[%s] dtnsi:[%s] dtkvt:[%s]>' % (
            self.__tablename__,
            self.nsch and str(self.nsch) or n_a, 
            self.kvt,
            getDate(self.dtizm, UTC_EASY_TIMESTAMP),
            getDate(self.dtnsi, UTC_EASY_TIMESTAMP),
            getDate(self.dtkvt, UTC_EASY_TIMESTAMP),
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(nsch=id).first()
    @property
    def get_division(cls):
        return cls.division
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls).order_by(cls.nsch)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.nsch)
        if is_query:
            return query
        return query.all()


class Speed(db.Model, ExtClassMethods):

    """
        10. Максимальная скорость соединений
    """
    __tablename__ = 'tvmax'

    # 1. SPEED ID
    kvmax = db.Column(db.BigInteger, Line_seq, primary_key=True, server_default=Speed_seq.next_value())
    # 2. NODE ID (FK)
    kuo = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 3. NODE ID (?, FK)
    kuon = db.Column(db.BigInteger, db.ForeignKey('tuo.kuo'), index=True)
    # 4. SPEED VALUE
    vmax = db.Column(db.Integer)

    speed1 = db.relationship('Node', backref=db.backref('suo1', lazy='dynamic'), uselist=True, foreign_keys=kuo)
    speed2 = db.relationship('Node', backref=db.backref('suo2', lazy='dynamic'), uselist=True, foreign_keys=kuon)

    def __init__(self, pk=None, kuo=None, kuon=None, **kw):
        super(Line, self).__init__(**kw)
        if pk is not None:
            self.kvmax = pk
        if kuo is not None:
            self.kuo = kuo
        if kuon is not None:
            self.kuon = kuon

    def __repr__(self):
        return '<Line[%s] pk:%s [%s-%s] state:[%s]>' % (
            self.__tablename__,
            self.ksd and str(self.ksd) or n_a, 
            self.kuo,
            self.kuon,
            self.vmax,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kvmax=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls).order_by(cls.kvmax)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.kvmax)
        if is_query:
            return query
        else:
            return query.all()


class Chain(db.Model, ExtClassMethods):

    """
        11. Цепочка сообщений
    """
    __tablename__ = 'tcepsb'

    # 1. CHAIN ID
    ksepsb = db.Column(db.BigInteger, Line_seq, primary_key=True, server_default=Chain_seq.next_value())
    # 2. MESSAGE-1 ID (FK)
    ksb1 = db.Column(db.BigInteger, db.ForeignKey('tsb.ksb'), index=True)
    # 3. MESSAGE-2 ID (FK)
    ksb2 = db.Column(db.BigInteger, db.ForeignKey('tsb.ksb'), index=True)
    # 4. MESSAGE-3 ID (FK)
    ksb3 = db.Column(db.BigInteger, db.ForeignKey('tsb.ksb'), index=True)

    chain1 = db.relationship('Message', backref=db.backref('muo1', lazy='dynamic'), uselist=True, foreign_keys=ksb1)
    chain2 = db.relationship('Message', backref=db.backref('muo2', lazy='dynamic'), uselist=True, foreign_keys=ksb2)
    chain3 = db.relationship('Message', backref=db.backref('muo3', lazy='dynamic'), uselist=True, foreign_keys=ksb3)

    def __init__(self, pk=None, ksb1=None, ksb2=None, **kw):
        super(Line, self).__init__(**kw)
        if pk is not None:
            self.ksepsb = pk
        if kuo is not None:
            self.ksb1 = kuo
        if kuon is not None:
            self.ksb2 = kuon

    def __repr__(self):
        return '<Line[%s] pk:%s [%s-%s-%s]>' % (
            self.__tablename__,
            self.ksepsb and str(self.ksepsb) or n_a, 
            self.ksb1,
            self.ksb2,
            self.ksb3,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(ksepsb=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.ksepsb)
        if is_query:
            return query
        else:
            return query.all()


class Signal(db.Model, ExtClassMethods):
    
    """
        12. Служебные сообщения
    """
    __tablename__ = 'tslsb'

    # 1. SIGNAL ID
    kslsb = db.Column(db.BigInteger, Line_seq, primary_key=True, server_default=Signal_seq.next_value())
    # 2. MESSAGE-1 ID (FK)
    kvsdo = db.Column(db.BigInteger, db.ForeignKey('tsb.ksb'), index=True)
    # 3. MESSAGE-2 ID (FK)
    ksbo = db.Column(db.BigInteger, db.ForeignKey('tsb.ksb'), index=True)

    signal1 = db.relationship('Message', backref=db.backref('suo1', lazy='dynamic'), uselist=True, foreign_keys=kvsdo)
    signal2 = db.relationship('Message', backref=db.backref('suo2', lazy='dynamic'), uselist=True, foreign_keys=ksbo)

    def __init__(self, pk=None, kvsdo=None, ksbo=None, **kw):
        super(Line, self).__init__(**kw)
        if pk is not None:
            self.kslsb = pk
        if kuo is not None:
            self.kvsdo = kvsdo
        if kuon is not None:
            self.ksbo = ksbo

    def __repr__(self):
        return '<Line[%s] pk:%s [%s-%s]>' % (
            self.__tablename__,
            self.kslsb and str(self.kslsb) or n_a, 
            self.kvsdo,
            self.ksbo,
            )

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(kslsb=id).first()
    @classmethod
    def ordered_rows(cls, is_query=None, **kw):
        query = db.session.query(cls).order_by(cls.kslsb)
        query = _set_filter(query, **kw)
        query = query.order_by(cls.kslsb)
        if is_query:
            return query
        else:
            return query.all()


## ==================================================== ##

def registerConfigChange(data, login):
    IsOk = False
    user = User.get_by_login(login)
    ob = ConfigChange(user)
    #ob.lgn = login
    #ob.dticfg = getDate(timestamp, UTC_EASY_TIMESTAMP)
    ob.fragd = data.get('before')
    ob.fragp = data.get('after')

    try:
        db.session.add(ob)
        _commit(True)
        IsOk = True
    except:
        raise

    if IsDeepDebug:
        print('--> ConfigChange.register.OK:%s %s' % (IsOk, repr(ob)))

    return IsOk

def deleteConfigChange(pk):
    IsOk = False
    ob = None
    if pk:
        ob = ConfigChange.get_by_id(pk)

    if ob is not None:
        db.session.delete(ob)
        is_error,errors =_commit(True)
    
    IsOk = not is_error

    if IsDeepDebug:
        print('--> ConfigChange.delete.OK:%s %s' % (IsOk, pk))

    return IsOk

def registerDivision(pk, command, **kw):
    pass

def registerMessageType(pk, command, **kw):
    if pk is not None and command == 'update':
        ob = MessageType.get_by_id(pk)
    else:
        ob = MessageType(pk)

    ob.itsb = kw.get('itsb')
    ob.prior = int(kw.get('prior') or 0)

    if command == 'create':
        db.session.add(ob)

    is_error, errors = _commit(True)

    IsOk = not is_error

    if IsTrace:
        print_to(None, '--> MessageType.register.OK:%s[%s] %s' % (IsOk, is_error, pk))

    return is_error, errors

def registerNode(pk, command, **kw):
    if pk is not None:
        ob = Node.get_by_id(pk)
    else:
        ob = Node(pk)

    if 'nsch' in kw:
        ob.nsch = kw.get('nsch')
    if 'ip' in kw and kw.get('ip'):
        ob.ip = kw['ip']
    if 'port1' in kw and kw.get('port1'):
        ob.port1 = decimal.Decimal(kw['port1'])
    if 'port2' in kw and kw.get('port2'):
        ob.port2 = decimal.Decimal(kw['port2'])
    if 'kikts' in kw:
        ob.kikts = kw.get('kikts')
    if 'pikts' in kw:
        ob.pikts = kw.get('pikts')
    if 'suo' in kw:
        ob.suo = decimal.Decimal(kw.get('suo'))

    if command == 'create':
        db.session.add(ob)

    is_error, errors = _commit(True)
    
    IsOk = not is_error

    if IsTrace:
        print_to(None, '--> Node.register.OK:%s[%s] %s' % (IsOk, is_error, pk))

    return is_error, errors

def registerLine(pk, command, **kw):
    pass

def registerLineState(pk, command, **kw):
    pass

def registerMessage(pk, command, **kw):
    pass

def registerBind(pk, command, **kw):
    pass

def set_local_node(statement, args):
    local_node = args and args.get('local_node') or ''
    if ':local_node:' in statement:
        statement = statement.replace(':local_node:', local_node and ('=%s' % local_node) or ' is not null')
    return statement

def get_where(items):
    where = ''
    if items:
        where = 'where %s' % ' and '.join(['(%s)' % x for x in items])

    if IsDebug and where:
        print_to(None, '\n>>> models.get_where: %s' % where)
    return where

def get_subwhere(items):
    where = ''
    if items:
        where = 'and %s' % ' and '.join(['(%s)' % x for x in items])

    if IsDebug and where:
        print_to(None, '\n>>> models.get_subwhere: %s' % where)
    return where

def set_filter(statement, args, mode=None):
    if IsDebug:
        print_to(None, '>>> set_filter.args: %s' % args)

    items = []
    subitems = []
    if args is not None:
        date = args.get('selected_date') and args['selected_date']

        selected_date = getDate(date, format=LOCAL_EASY_DATESTAMP, is_date=True) and date or None
        if selected_date is not None:
            if mode == 'linestates':
                items.append("dtsd >= '%s 00:00:00'" % selected_date)
                items.append("dtsd <= '%s 23:59:59'" % selected_date)
            elif mode == 'messages':
                subitems.append("dtosb >= '%s 00:00:00'" % selected_date)
                subitems.append("dtosb <= '%s 23:59:59'" % selected_date)

        selected_node = args.get('selected_node') or None
        if mode == 'lines':
            #items.append("line.kuo is not null and line.kuov is not null")
            pass
        elif mode == 'linestates':
            #items.append('line.kuo is not null and line.kuov is not null')
            if selected_node:
                items.append('line.kuo=%s or line.kuo=%s' % (selected_node, selected_node))
        elif mode == 'messages':
            pass

        selected_line = args.get('selected_line') and args['selected_line'] or None
        if selected_line is not None:
            ksd = node1 = node2 = line = None
            if isIterable(selected_line) and len(selected_line) == 2:
                node1 = int(selected_line[0])
                node2 = int(selected_line[1])
                line = '(%s, %s)' % (node1, node2)
            else:
                ksd = int(selected_line)
            if mode == 'lines':
                items.append('linestate.ksd=%s' % ksd)
            elif mode == 'linestates':
                if ksd:
                    items.append('linestate.ksd=%s' % ksd)
            elif mode == 'messages':
                if line:
                    subitems.append('kuoo in %s or kuop in %s' % (line, line))

    where = get_where(items)
    subwhere = get_subwhere(subitems)
    scheme = connection_params.scheme
    statement = re.sub(r':scheme:', scheme, re.sub(r':where:', where, re.sub(r':subwhere:', subwhere, statement)))

    if IsDebug:
        print_to(None, '>>> set_filter.statement: \n%s' % statement)

    return set_local_node(statement, args)

def get_activity_dates(args):
    statement = \
    """
        select distinct to_char(dtsd, 'YYYY-MM-DD') as date 
        from :scheme:.tvsd 
        order by date asc
    """

    statement = set_local_node(statement.replace(':scheme:', connection_params.scheme), args)

    query = db.session.query('date').from_statement(text(statement))
    
    for row in query.all():
        yield row

def get_messages_dates(args):
    statement = \
    """
        select distinct to_char(dtosb, 'YYYY-MM-DD') as date from :scheme:.tsb 
        where kuo:local_node: and dtosb is not null
        order by date asc
    """

    statement = set_local_node(statement.replace(':scheme:', connection_params.scheme), args)

    query = db.session.query('date').from_statement(text(statement))
    
    for row in query.all():
        yield row

def get_center_messages_period():
    return db.session.query(func.min(Message.dtosb), func.max(Message.dtosb)).first()

def get_branch_messages_period():
    return db.session.query(func.min(Message.dtosb), func.max(Message.dtosb)).first()

def gen_lines(args=None, **kw):
    statement = \
    """
        select distinct line.ksd,
        (
            select (select isch from :scheme:.tsch where node.nsch=tsch.nsch) || ':' || pikts
            from :scheme:.tuo as node where node.kuo=line.kuo)
        || ' - ' ||
        (
            select (select isch from :scheme:.tsch where node.nsch=tsch.nsch) || ':' || pikts
            from :scheme:.tuo as node where node.kuo=line.kuov) as line
        from :scheme:.tvsd as linestate
        inner join :scheme:.tsd as line on line.ksd=linestate.ksd
        where line.kuov:local_node:
        order by ksd;
    """

    statement = set_filter(statement, args, mode='lines')

    query = db.session.query('ksd','line').from_statement(text(statement))
    
    for row in query.all():
        yield row

def gen_local_lines(args=None, **kw):
    statement = \
    """
        select distinct line.ksd,
        (
            select (select isch from :scheme:.tsch where node.nsch=tsch.nsch) || ':' || pikts
            from :scheme:.tuo as node where node.kuo=line.kuo)
        as line
        from :scheme:.tvsd as linestate
        inner join :scheme:.tsd as line on line.ksd=linestate.ksd
        where line.kuov:local_node:
        order by ksd;
    """

    statement = set_filter(statement, args, mode='lines')

    query = db.session.query('ksd','line').from_statement(text(statement))
    
    for row in query.all():
        yield row

def gen_activities(args, **kw):
    #"""select distinct to_char(dtsd, ' HH:MI:SS DD-MM-YY') as date, 
    statement = \
    """
    select dtsd as date, linestate.ksd, kuo, kuov, ssd,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=line.kuo
    ) as node1,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=line.kuov
    ) as node2,
    (
        select node.nsch || '_' || node.nsch || nkts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=line.kuo
    ) || '-' ||
    (
        select node.nsch || '_' || node.nsch || nkts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=line.kuov
        ) as code
    from :scheme:.tvsd as linestate
    inner join :scheme:.tsd as line on line.ksd=linestate.ksd 
    :where:
    order by code, date desc
    """

    statement = set_filter(statement, args, mode='linestates')
    
    query = db.session.query('date', 'ksd', 'kuo', 'kuov', 'ssd', 'node1', 'node2', 'code').from_statement(text(statement))
    
    for row in query.all():
        yield row

def gen_reliabilities(args, **kw):
    statement = \
    """
    select dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd,
    (
        select (select isch from :scheme:.tsch where node.nsch=tsch.nsch) || ':' || kikts
        from :scheme:.tuo as node where node.kuo=line.kuo
    ) as node1,
    (
        select (select isch from :scheme:.tsch where node.nsch=tsch.nsch) || ':' || kikts
        from :scheme:.tuo as node where node.kuo=line.kuov
    ) as node2
    from :scheme:.tvsd as linestate 
    inner join :scheme:.tsd as line on line.ksd=linestate.ksd 
    :where: 
    order by date, kuo, kuov
    """

    statement = set_filter(statement, args, mode='linestates')

    query = db.session.query('date', 'ksd', 'kuo', 'kuov', 'ssd', 'node1', 'node2').from_statement(text(statement))
    
    for row in query.all():
        yield row

def gen_capacities(args, **kw):
    statement = \
    """
    select node, mtype, nodes.pikts as line, 
      messagetypes.itsb as messagetype, 
      sum(c1)::text||'-'||sum(c2)::text as capacity, 
      sum(s1)::text||'-'||sum(s2)::text as volume 
    from
    (
     (select kuopr as node, ktsb as mtype, count(*) as c1, 0 as c2, sum(ldata) as s1, 0 as s2 from orion.tsb
      where kuo:local_node: and kuopr is not null :subwhere:
      group by kuopr, ktsb)
      union
     (select kuosl as node, ktsb as mtype, 0 as c1, count(*) as c2, 0 as s1, sum(ldata) as s2 from orion.tsb
      where kuo:local_node: and kuosl is not null :subwhere:
      group by kuosl, ktsb)
    ) as capacities
     inner join orion.tuo as nodes on capacities.node=nodes.kuo
     inner join orion.ttsb as messagetypes on capacities.mtype=messagetypes.ktsb
     group by node, mtype, line, ktsb, messagetype
     order by node, mtype, line, ktsb, messagetype
    """

    statement = set_filter(statement, args, mode='messages')

    query = db.session.query('node', 'mtype', 'line', 'messagetype', 'capacity', 'volume').from_statement(text(statement))
    
    for row in query.all():
        yield row

def gen_speeds(args, **kw):
    statement = \
    """
    select node, 
        nodes.pikts as line,
        sum(s1+s2) as volume,
        round(cast(float8 (sum(dtime) ) as numeric), 2) as time,
        round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed,
        sum(errors) as errors
    from
    (
     (select kuop as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
      abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
      sum(case when kvt1=0 then 1 else 0 end) as errors
      from orion.tsb
      where kuo:local_node: and kuop is not null and kuoo is not null and dtosb is not null and dtpsb is not null :subwhere:
      group by kuop, dtpsb, dtosb)
      union
     (select kuoo as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
      abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
      sum(case when kvt2=0 then 1 else 0 end) as errors
      from orion.tsb
      where kuo:local_node: and kuoo is not null and kuop is not null and dtosb is not null and dtpsb is not null :subwhere:
      group by kuoo, dtpsb, dtosb)
    ) as capacities
     inner join orion.tuo as nodes on capacities.node=nodes.kuo
     :where:
     group by node, line
     order by node, line;
    """

    statement = set_filter(statement, args, mode='messages')

    query = db.session.query('node', 'line', 'volume', 'time', 'speed', 'errors').from_statement(text(statement))
    
    for row in query.all():
        yield row

def get_linestates_period():
    return db.session.query(func.min(LineState.dtsd), func.max(LineState.dtsd)).first()

def nodes_forced_refresh(**kw):
    nsch = int(kw.get('nsch'))
    nkts = int(kw.get('nkts'))
    suo = int(kw.get('state'))
    timedelta = int(kw.get('timedelta'))
    
    query = db.session.query(Node) \
        .filter_by(nsch=nsch) \
        .filter_by(nkts=nkts) \
        .filter_by(suo=suo)

    now = getToday()

    ids = []
    is_done = 0

    for node in query.all():
        delta = getTimedelta(now, node.dtuo)
        if timedelta < delta:
            continue

        node.suo = 2
        node.dtuo = now
        ids.append(node.pk)
        is_done = 1

    is_error, errors = 0, []

    if is_done:
        is_error, errors = _commit(True)
    
    IsOk = not is_error

    if IsTrace:
        print_to(None, '--> Nodes_forced_refresh.OK:%s[%s] ids:%s' % (IsOk, is_error, ids))

    return is_done, is_error, errors

def gen_center_exchange(args, **kw):
    statement = \
    """
    select ksb as pk, messagetypes.itsb as messagetype, ldata as size, lgn as login, 
        dtosb as sent, dtpsb as received, kvt1 as r1, kvt2 as r2,
        dtokvt1 as dater1, dtpkvt2 as dater2,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=messages.kuo
    ) as node,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=messages.kuoo
    ) as sender,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=messages.kuop
    ) as receiver,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=messages.kuopr
    ) as before,
    (
        select division.isch || ':' || kikts
        from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
        where node.kuo=messages.kuosl
    ) as after,
    kuo, kuoo, kuop, kuopr, kuosl, ns, 'ksb', 'kuo', 'kuoo', 'kuop', 'kuopr', 'kuosl'
    from :scheme:.tsb as messages
    inner join :scheme:.ttsb as messagetypes on messagetypes.ktsb=messages.ktsb
    :where:
    order by messages.dtpsb desc
    """

    statement = set_filter(statement, args, mode='messages')
    
    query = db.session.query('pk', 'messagetype', 'size', 'login', 
    'sent', 'received', 'r1', 'r2', 'dater1', 'dater2', 'node', 'sender', 
    'receiver', 'before', 'after', 'kuo', 'kuoo', 'kuop', 'kuopr', 'kuosl', 'ns', 'ksb', 'kuo', 'kuoo', 'kuop', 'kuopr', 'kuosl').from_statement(text(statement))

    query = _set_offset(query, **kw)
    
    for row in query.all():
        yield row

def gen_branch_exchange(args):
    statement = \
        """
        select ksb, messagetypes.itsb as messagetype, 
        (
            select division.isch || ':' || kikts
            from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuo
        ) as node,
        (
            select division.isch || ':' || kikts
            from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuoo
        ) as sender,
        (
            select division.isch || ':' || kikts
            from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuop
        ) as receiver,
        (
            select division.isch || ':' || kikts
            from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuopr
        ) as prevnode,
        (
            select division.isch || ':' || kikts
            from :scheme:.tuo as node inner join :scheme:.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuosl
        ) as nextnode,
        kuo, kuoo, kuop, kuopr, kuosl,
        ns, lgn, messages.ktsb, ldata, dtosb, dtpsb,
        kvt1, dtokvt1, kvt2, dtpkvt2
        from :scheme:.tsb as messages
        inner join :scheme:.ttsb as messagetypes on messagetypes.ktsb=messages.ktsb
        order by messages.dtpsb desc
        """

    statement = set_filter(statement, args)
    
    query = db.session.query(
        'ksb', 'node', 'sender', 'receiver', 'prevnode', 'nextnode', 
        'kuo', 'kuoo', 'kuop', 'kuopr', 'kuosl', 
        'ns', 'lgn', 'ktsb', 'ldata', 'dtosb', 'dtpsb', 
        'kvt1', 'dtokvt1', 'kvt2', 'dtpkvt2'
        ).from_statement(text(statement))
    
    for row in query.all():
        yield row

## ==================================================== ##

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_view_users(id, page=1, per_page=DEFAULT_PER_PAGE, **kw):
    context = clean(kw.get('context') or '')

    query = db.session.query(User) #query = User.query

    where = kw.get('where')

    if where:
        is_joined = 0

        for k in where.keys():
            v = where[k]

            if v is None or v == -1:
                continue

            if not is_joined and k in ('subdivision_id', 'app_role_id', 'app_privilege'):
                query = query.join(Privileges)
                is_joined = 1

            if not k:
                pass
            elif k == 'subdivision_id':
                query = query.filter(Privileges.subdivision_id==v)
            elif k == 'app_role_id':
                query = query.filter(Privileges.role==v)
            elif k == 'app_privilege':
                if v == 1:
                    query = query.filter(Privileges.is_manager==1)
                if v == 2:
                    query = query.filter(Privileges.is_consultant==1)
                if v == 3:
                    query = query.filter(Privileges.is_author==1)
            elif k == 'role_id':
                query = query.filter(User.role==v)
            elif k == 'confirmed':
                query = query.filter(User.confirmed==v)
            elif k == 'enabled':
                query = query.filter(User.enabled==v)

    if context:
        c = '%' + context + '%'

        keys = ('login', 'first_name', 'family_name', 'last_name', 'email',)
        conditions = []

        for key in keys:
            conditions.append(getattr(User, key).ilike(c))
        query = query.filter(or_(*conditions))

    order = kw.get('order')

    if order:
        if order == 'fio':
            query = query.order_by(User.family_name).order_by(User.first_name).order_by(User.last_name)
        else:
            query = query.order_by(
                order == 'login' and User.login or 
                order == 'email' and User.email or 
                order == 'role' and User.role or 
                order == 'post' and User.post or
                User.id
                )

    total = query.count()
    offset = per_page*(page-1)

    if offset > 0:
        query = query.offset(offset)
    query = query.limit(per_page)
    items = query.all()

    mode = kw.get('mode') or 0
    selected = ''

    users = []
    for ob in items:
        if mode:
            user = [ob.id, ob.login, ob.full_name(), ob.post, ob.email, roles[ob.role], ob.is_active and 'Y' or 'N', 
                ob.enabled and 'Y' or 'N', False]
            if mode == 2:
                users.append(UserRecord._make(user)) # yield UserRecord._make(user)
            else:
                users.append(user)
        else:
            users.append(ob.get_data('view', id=id))
            if not selected:
                selected = users[-1].get('selected')

    if not selected and len(users) > 0 and not mode:
        users[0]['selected'] = 'selected'

    if not mode:
        return Pagination(page, per_page, total, users, query)
    return users

def get_users(key=None, is_ob=None):
    users = []
    for ob in User.all():
        if not (ob.is_active and ob.enabled and ob.email): # and ob.subdivision_id
            continue
        if is_ob:
            users.append(ob)
        else:
            users.append((
                ob.login,
                ob.full_name(),
                ob.short_name(),
                ob.post or '',
                ob.email,
                ob.subdivision_id,
                ob.subdivision_code,
                ob.subdivision_name,
                ob.id,
                ob.enabled,
            ))
    if is_ob:
        return sorted(users, key=lambda x: x.full_name())
    return sorted(users, key=itemgetter(key is None and 1 or key or 0))

def get_users_dict(key=None, as_dict=None):
    if as_dict:
        return dict([(x[0], dict(zip(['full_name', 'short_name', 'post', 'email', 'subdivision_id', 'subdivision_code', 'subdivision_name', 'id', 'enabled'], x[1:]))) for x in get_users(key)])
    return [dict(zip(['login', 'full_name', 'short_name', 'post', 'email', 'subdivision_id', 'subdivision_code', 'subdivision_name', 'id', 'enabled'], x)) for x in get_users(key)]

def print_users(key=None):
    for x in get_users_dict(key):
        print(('%3d: %s %s %s %s %s %s' % (
            x['id'], 
            x['subdivision_code'], 
            x['subdivision_name'], 
            x['login'], 
            x['full_name'], 
            x['post'], 
            x['email'], 
            )).encode(default_print_encoding, 'ignore').decode(default_print_encoding))

def register_user(form, id=None):
    IsOk = False
    errors = []

    if form is not None and form.validate():
        if id:
            user = User.get_by_id(id)
        else:
            user = User(form.login.data)

        if not id and form.login.data and User.get_user_by_login(form.login.data):
            errors.append( \
                'User with given login exists!')
            IsOk = False
        else:
            IsOk = True

    if IsOk:
        user.set_name((form.first_name.data, form.last_name.data, form.family_name.data,))
        user.role = form.role.data
        user.post = 'post' in form and form.post.data or ''
        user.email = 'email' in form and form.email.data or ''
        user.confirmed = 'confirmed' in form and form.confirmed.data or None
        user.enabled = 'enabled' in form and form.enabled.data or None

        if user.login != form.login.data and form.login.data:
            user.login = form.login.data

        if form.password.data and form.password.data != password_mask:
            user.password = form.password.data

        if user.confirmed is None:
            user.confirmed = True

        if user.enabled is None:
            user.enabled = True

        if not id:
            db.session.add(user)

        _commit(True)

    if IsDeepDebug:
        print('--> OK:%s %s' % (IsOk, form.errors))

    return IsOk, user, errors

def delete_user(id):
    user = User.get_by_id(id)

    if user:
        db.session.delete(user)
        db.session.commit()

def local_reflect_meta():
    meta = MetaData()
    meta.reflect(bind=db.engine)
    return meta

def drop_table(cls):
    cls.__table__.drop(db.engine)

def show_tables():
    return local_reflect_meta().tables.keys()

def print_tables():
    for x in db.get_tables_for_bind():
        print(x)

def show_all():
    return local_reflect_meta().sorted_tables

def get_app_roles():
    return [x for x in list(app_roles) if x[1]]

def get_roles():
    return [x for x in list(roles) if not x[1].startswith('X')]

def get_subdivisions(order=None):
    if order is None or order == 'name':
        order = Subdivision.name
    elif order == 'code':
        order = Subdivision.code
    query = Subdivision.query.order_by(order)
    return [(ob.id, ob.code, ob.name, ob.manager, ob.fullname) for ob in query.all()]

def print_subdivisions(order=None):
    for x in get_subdivisions(order):
        print(('%4d: %s %s %s %s' % x).encode(default_print_encoding, 'ignore').decode(default_print_encoding))

## ==================================================== ##

def load_system_config(user=None):
    g.system_config = make_config('system_config.attrs')

    if not user:
        user = current_user

    login = not user.is_anonymous and user.is_authenticated and user.login or ''

    x = list(filter(None, g.system_config.USE_REVIEWER_AVATAR or []))
    g.system_config.IsUseReviewerAvatar = 1 if login in x or '*' in x else 0

    x = list(filter(None, g.system_config.LIMITED_LENGTH_EXCLUDE or []))
    g.system_config.IsLimitedLengthExclude = 1 if login in x or '*' in x else 0

    g.system_config.DEFAULT_CREATED_AFTER = getDate(g.system_config.DEFAULT_CREATED_AFTER or '2020-01-01', 
        format=LOCAL_EASY_DATESTAMP, is_date=True)

def send_email(subject, html, user, addr_to, addr_cc=None, addr_from=None):
    if not html or not addr_to:
        return 0

    def _send(subject, html, _to, _cc, _from):
        timestamp = getDate(getToday(), format=UTC_FULL_TIMESTAMP)

        done = 1

        try:
            if not IsNoEmail:
                done = send_simple_mail(subject, html, _to, addr_cc=_cc, addr_from=_from, 
                    with_sleep=g.system_config.EMAILS_TIMEOUT or 3,
                    with_trace=0
                    )
        except:
            if IsPrintExceptions:
                print_exception()

        if IsTrace:
            print_to(None, '>>> mail sent %s, login:%s, to:%s, cc:%s, from:%s, subject: [%s], done:%s' % (timestamp, 
                user and user.login or '...', _to, _cc, _from, subject, done))

        return done

    def _get_addrs(emails):
        return emails and ';'.join(emails) or ''

    is_error = 0

    cc = _get_addrs(addr_cc)
    emails = []

    limit = g.system_config.EMAILS_ADDR_TO_LIMIT or 0
    exclude_emails = g.system_config.EXCLUDE_EMAILS or []

    for email in [x.strip() for x in addr_to]:
        if not email or email in emails or email in exclude_emails:
            continue
        elif ';' in email:
            if not _send(subject, html, _get_addrs(email.split(';')), cc, addr_from):
                is_error = 1
        elif not limit or len(emails) < limit:
            emails.append(email)
        else:
            if not _send(subject, html, _get_addrs(emails), cc, addr_from):
                is_error = 1
            emails = []

    if emails:
        if not _send(subject, html, _get_addrs(emails), cc, addr_from):
            is_error = 1

    return not is_error and 1 or 0

def gen_subdivisions():
    items = [
        ('0001', 'Администрация', '', ''),
    ]

    def find(code):
        return Subdivision.query.filter_by(code=code).first()

    for item in items:
        code, name, manager, fullname = item

        ob = find(code)

        if ob is None:
            ob = Subdivision(code, name, manager, fullname)
        else:
            ob.name = name
            ob.manager = manager
            ob.fullname = fullname

        db.session.add(ob)

    _commit()
