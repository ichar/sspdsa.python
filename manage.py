#!flask/bin/python

import os
from app import create_app, db
from flask import url_for
from flask_script import Server, Manager, Shell
from config import connection_params, setup_console, isIterable
from sqlalchemy import func, asc, desc, and_, or_


from app.models import (
     APP_SEQUENCES,
     Pagination, Sequence,
     User, Photo, Settings, Subdivision, Privileges, 
     ConfigChange, Division, Node, MessageType, Message, Line, LineState, Equipment, Bind, Speed, Chain, Signal,
     registerConfigChange, deleteConfigChange,
     admin_view_users, get_users, get_users_dict, print_users, drop_table, show_tables, print_tables, show_all, 
     gen_subdivisions, get_subdivisions, print_subdivisions,
     app_roles, get_app_roles, gen_lines
)

from app.database import database_config

connection_params._init_state()

app = create_app(os.getenv('APP_CONFIG') or 'default') # 'production'

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

def routes(link=None):
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    sorted(links)
    if link:
        links = [x for x in links if link in x[1]]
    return links

def print_routes(link=None):
    for url in routes(link=link):
        print(url)

def print_metadata():
    for n, x in enumerate(db.metadata.tables.keys()):
        print('>>> %s. %s' % (n+1, x))

def print_mapper(ob=None):
    if ob is None:
        print('!!! Class should be present: ob (Node, Message... or an instance)')
        return
    for n, x in enumerate(ob.__mapper__.__dict__):
        print('>>> %s. %s' % (n+1, str(x)))

def print_table_columns(ob=None):
    if ob is None:
        print('!!! Class should be present: ob (Node, Message... or an instance)')
        return
    for n, x in enumerate(ob.__table__.columns):
        print('>>> %s. %s' % (n+1, str(x.key)))

def rows(ob, key=None, pk=None, obs=None):
    #
    # rows(Node, 'nodes')
    # rows(LineState, 'linestates')
    #
    if obs is None:
        obs = ob.get_rows(database_config.get(key))
    for n, x in enumerate(obs):
        if not pk or (pk and x['ID'] == pk):
            print('... %s: %s' % (n, x))

def ordered_rows(ob, pk=None):
    for n, x in enumerate(ob.ordered_rows()):
        if not pk or (pk and x['ID'] == pk):
            print('... %s: %s' % (n, x))

def print_mapping(obs):
    #
    # rows=Node.get_rows(database_config['nodes'], obs=Node.nodes())
    # rows=Line.get_rows(database_config['lines'], obs=Line.lines(), as_is=True)
    # print_mapping(rows)
    #
    keys = obs[0].keys()
    for n, ob in enumerate(obs):
        for key in keys:
            print('>>> %s: %s=[%s]' % (n+1, key, ob[key]))

manager = Manager(app)

#setup_console()

def make_shell_context():
    return dict(
            APP_SEQUENCES=APP_SEQUENCES,
            app=app, db=db, 
            Pagination=Pagination, func=func, asc=asc, desc=desc, and_=and_, or_=or_,
            User=User, Photo=Photo, Settings=Settings, Subdivision=Subdivision, Privileges=Privileges,
            ConfigChange=ConfigChange, Division=Division, Node=Node, MessageType=MessageType, Line=Line, LineState=LineState, Equipment=Equipment, 
            Message=Message, Bind=Bind, Speed=Speed, Chain=Chain, Signal=Signal,
            registerConfigChange=registerConfigChange, deleteConfigChange=deleteConfigChange,
            admin_view_users=admin_view_users, get_users=get_users, get_users_dict=get_users_dict, print_users=print_users,
            drop_table=drop_table, show_tables=show_tables, print_tables=print_tables, show_all=show_all, 
            gen_subdivisions=gen_subdivisions, get_subdivisions=get_subdivisions, print_subdivisions=print_subdivisions,
            app_roles=app_roles, get_app_roles=get_app_roles, database_config=database_config, gen_lines=gen_lines,
            isIterable=isIterable, routes=routes, print_routes=print_routes, url_for=url_for, 
            print_metadata=print_metadata, print_mapper=print_mapper, print_table_columns=print_table_columns,
            rows=rows, ordered_rows=ordered_rows, print_mapping=print_mapping
        )

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("start", Server(host='0.0.0.0', port=8000, debug=True, use_debugger=True, use_reloader=True))


@manager.command
def test(coverage=False):
    """Run the unit tests."""

    return True

@manager.command
def profile(length=20, profile_dir=None):
    """Start the application under the code profiler."""
    #app.config['PROFILE'] = True
    #from werkzeug.contrib.profiler import ProfilerMiddleware
    #app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    #app.run()
    pass

@manager.command
def deploy():
    """Run deployment tasks."""
    #from flask.ext.migrate import upgrade
    # migrate database to latest revision
    #upgrade()
    pass

@manager.command
def start():
    """Run server."""
    #app.run(host='0.0.0.0', port=5000, ssl_context='adhoc', debug=True)
    app.run(host='0.0.0.0', port=5000, ssl_context=None, debug=True, use_debugger=True, use_reloader=True)


if __name__ == '__main__':
    #connection_params._init_state()
    manager.run()
