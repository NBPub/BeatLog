from .ops_report import table_build
from .models import RegexMethod
from datetime import datetime
from psycopg import sql

def vacuum_tables(tables):
    try:
        from .db_pool import conninfo
        import psycopg # autocommit connection for Vacuum
        with psycopg.connect(conninfo, autocommit=True) as conn:
            cur = conn.cursor() 
            for table in tables:
                cur.execute(sql.SQL('VACUUM {};').format(sql.Identifier(table)))            
        return ('garbage collected!','success')
    except Exception as e:
        return (str(e), 'danger')

def log_data_cleaning(cur):
    SQL = '''SELECT relname, reltuples::int FROM pg_class WHERE relname IN 
    ('access','error', 'fail2ban') AND reltuples > 0 ORDER BY relname'''
    logs = {val[0]:"{:,}".format(val[1]) for val in cur.execute(SQL).fetchall()} # log:#rows for log's with records 
    if logs == {}:
        return None, None
    data = [] # first record, last record, estimated size for table
    prefill = None
    for log in logs.keys():      
        stop = cur.execute(sql.SQL('SELECT date FROM {} ORDER BY date desc LIMIT 1').format(sql.Identifier(log))).fetchone()
        stop = stop[0].strftime('%x %X') if stop else '' 
        start = cur.execute(sql.SQL('SELECT date FROM {} ORDER BY date LIMIT 1').format(sql.Identifier(log))).fetchone()
        if prefill:
            prefill = start[0] if start and start[0] < prefill else prefill
        else:
            prefill = start[0] if start else None
        start = start[0].strftime('%x %X') if start else ''
        size = cur.execute('SELECT pg_size_pretty( pg_total_relation_size(%s));', (log,)).fetchone()[0]
        data.append((log, logs[log], start, stop, size))
    table = table_build(data, ['Log Name', 'Database Rows', 'First Entry', 'Last Entry', 'Estimated Size'],False)[0]
    return logs, table, prefill

def log_clean_estimate(cur,data):
    estimate = []
    if type(data[0]) == list:
        for log in data[0]:
            SQL = sql.SQL('SELECT COUNT(date) FROM {} WHERE date BETWEEN %s AND %s').format(sql.Identifier(log))
            estimate.append(cur.execute(SQL, (data[1], data[2])).fetchone()[0])
    else:
        SQL = sql.SQL('SELECT COUNT(date) FROM {} WHERE date BETWEEN %s AND %s').format(sql.Identifier(data[0]))
        estimate.append(cur.execute(SQL, (data[1], data[2])).fetchone()[0])
    return estimate if sum(estimate) > 0 else None
    
def log_clean_confirmed(conn,cur,data):
    logs = [data[0]] if type(data[0]) == str else data[0]
    message = []
    indicator = False
    for log in logs:
        SQL = sql.SQL("DELETE FROM {} WHERE date BETWEEN %s AND %s").format(sql.Identifier(log))
        with conn.transaction():    
            deleted = int(cur.execute(SQL, (data[1], data[2])).statusmessage[7:])    
        if deleted > 0:
            # update last parsed if needed, set back to 0 if none
            line = cur.execute(sql.SQL("SELECT date FROM {} ORDER BY date desc LIMIT 1").format(sql.Identifier(log))).fetchone()
            line = line[0] if line else datetime(1,1,1)
            lastParsed = cur.execute("SELECT lastparsed FROM logfiles WHERE name=%s", (log,)).fetchone()[0]
            if lastParsed[0] != line:
                cur.execute('UPDATE logfiles SET lastparsed=%s WHERE name=%s', ([line, lastParsed[1]], log))
            message.append((f'{deleted} rows deleted from {log}', 'success'))
            indicator = True
        else:
            message.append(('No data deleted!', 'warning'))
    return message, indicator
    
def geo_noIP_check(cur):
    SQL = '''SELECT COUNT(id) FROM geoinfo WHERE id NOT IN (
SELECT DISTINCT geo FROM (SELECT DISTINCT geo FROM error WHERE geo IS NOT NULL UNION ALL 
SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL) "tmp")'''
    check = cur.execute(SQL).fetchone()[0]
    return check if check > 0 else None                    
    
# Regex Methods - provide defaults
def populate_regex(conn, cur):
    methods = {
'access_primary':r'(?P<IP>\d+\.\d+.\d+.\d+) - .+ \[(?P<date>\d+\/[a-z]+\/\d+:\d+:\d+:\d+) -\d+\] "(?P<method>[a-z]+) (?P<URL>\S+) HTTP\/(?P<http>\d.\d)" (?P<status>\d+) (?P<bytes>\d+) "(?P<referrer>.+)" "(?P<tech>.*)"',
'access_secondary':r'(?P<IP>\d+\.\d+.\d+.\d+) - .+ \[(?P<date>\d+\/[a-z]+\/\d+:\d+:\d+:\d+) -\d+\] "(?P<URL>.*)" (?P<status>\d+) (?P<bytes>\d+) "(?P<referrer>.+)" "(?P<tech>.*)"',
'access_time':r'\d+\.\d+.\d+.\d+ - .+ \[(?P<time>\d+\/[a-z]+\/\d+:\d+:\d+:\d+) .*',
'error_primary':r'(?P<date>\d+\/\d+\/\d+ \d+:\d+:\d+) (?P<level>\[\w+\]) \d+#\d+: \*\d+(?P<message>.+), client: (?P<IP>\d+\.\d+.\d+.\d+), .*',
'error_secondary':r'(?P<date>\d+\/\d+\/\d+ \d+:\d+:\d+) (?P<level>\[\w+\]) \d+#\d+: (?P<message>.+), responder: r3.o.lencr.org, peer: (?P<IP>.+), .*',
'error_time':r'(?P<time>\d+\/\d+\/\d+ \d+:\d+:\d+) .*',
'fail2ban':r'(?P<date>\d+-\d+-\d+ \d+:\d+:\d+,\d+) fail2ban.\w+\s*\[\d+\]: (?P<level>\w+)\s* \[(?P<filter>.+)\] (?P<actionIP>.*)',
'fail2ban_time':r'(?P<time>\d+-\d+-\d+ \d+:\d+:\d+,\d+) .*',
        }  
    for key,val in methods.items():
        check = cur.execute('SELECT name FROM regex_methods WHERE name=%s', (key,)).fetchone()
        if not check:
            r = RegexMethod(key, val)
            SQL = "INSERT INTO regex_methods (name, pattern, groups) VALUES (%s, %s, %s)" 
            with conn.transaction():
                cur.execute(SQL, (key, val, r.groups))