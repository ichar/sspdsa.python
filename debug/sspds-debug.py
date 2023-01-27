
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from sqlalchemy import MetaData, create_engine

params = {
    'host'      : 'localhost',
    'dbname'    : 'sspds',
    'user'      : 'postgres',
    'password'  : 'admin',
    'schema'    : 'orion',
}
table = '%(schema)s.tuo' % params
where = 'kuo>0'
order = 'kuo'
limit = 1

IsDebug = 1
IsDeepDebug = 0
IsPrintAlchemy = 1
IsPrintPsycopg = 0
#
#   sqlalchemy
#
url = "postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s" % params
engine = create_engine(url,
            client_encoding="UTF-8",
            connect_args={'options': '-csearch_path=%(schema)s' % params}
    )
conn = engine.connect()
#
#   psycopg
#
connection = "host=%(host)s dbname=%(dbname)s user=%(user)s password=%(password)s" % params
ps_conn = psycopg2.connect(connection, options="-c search_path=%(schema)s" % params)

sql = 'SELECT * FROM %s WHERE %s ORDER BY %s LIMIT %s' % (
    table,
    where,
    order,
    limit
)

print(sql)


def print_msg(msg):
    print('%s %s:' % ('-'*20, msg))

def getMetadata(sql):
    #metadata = MetaData(bind=conn, reflect=True)
    #data = metadata.tables(table)
    ps_cursor = ps_conn.cursor(cursor_factory=RealDictCursor)
    ps_cursor.execute(sql)
    headers = [desc[0] for desc in ps_cursor.description]
    if IsDebug:
        print(headers)
    return headers

def getData(sql, headers):
    print_msg('SQLAlchemy')

    res = conn.execute(sql)
    data = res.fetchall()
    if IsDebug:
        print(len(data))

    for n, line in enumerate(data):
        if IsPrintAlchemy:
            #print('>>> %d %s' %(n, line))
            print('>>> row %d ' % n)
            for i, column in enumerate(line):
                print('>%d[%s]:%s' % (i,headers[i], str(column).strip())) #

    if IsDeepDebug:
        print('type data: %s' % type(data))
        print('type row: %s' % type(data[0]))
        #print(data[0])

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

headers = getMetadata(sql)
getData(sql, headers)

rows = getCursor(sql)

print('='*20)
print('rows total: %d' % len(rows))

if IsDeepDebug:
    row = rows[0]
    print(type(row))
    print(row.keys())
