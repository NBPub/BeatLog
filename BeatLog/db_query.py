from flask import (
    Blueprint, render_template, request, current_app#, redirect, url_for
)
from datetime import datetime, timedelta
from copy import copy
from psycopg import sql
from .db_pool import pool

SQL_statements = { 'basic': 'SELECT * FROM {}', 'geocheck': 'SELECT geo FROM {}',
                    'access':{
'httpv2':
'AND http==20',
'httpv1':
'AND http<20',
'ignorable':
'AND (status BETWEEN 400 AND 499 OR http<20)'
                             },
                    'error':{
'ip_version_TODO':
'',

                             },                           
}
# function date bound portion and date ordering sections of SQL statement
def add_date(dateOrder, date, query_type):
    if dateOrder == 'desc':
        if query_type != 'filtrate':
            d_seq = sql.SQL('WHERE date < {}').format(date)
            d_geo_seq = sql.SQL('WHERE geo IS NOT NULL AND date < {}').format(date)
        else:
            bound = date - timedelta(days=7)
            d_seq = sql.SQL('WHERE date BETWEEN {} AND {}').format(bound, date)
            d_geo_seq = sql.SQL('WHERE geo IS NOT NULL AND date BETWEEN {} AND {}').format(bound, date)
        later = sql.SQL('ORDER BY date desc')
    else:
        if query_type != 'filtrate':
            d_seq = sql.SQL('WHERE date > {}').format(date)
            d_geo_seq = sql.SQL('WHERE geo IS NOT NULL AND date > {}').format(date)
        else:
            bound = date + timedelta(days=7)
            d_seq = sql.SQL('WHERE date BETWEEN {} AND {}').format(date, bound)
            d_geo_seq = sql.SQL('WHERE geo IS NOT NULL AND date BETWEEN {} AND {}').format(date, bound)         
        later = sql.SQL('ORDER BY date asc')  
    return d_seq, d_geo_seq, later

# generate appropriate SQL strings based on settings (query, geocheck, nextcheck)
def db_query(log, query_type, dateOrder, date, rows, homeFilter, options, cur, cols):
    sequence = [sql.SQL(SQL_statements['basic']).format(sql.Identifier(log))]
    geo_seq = [sql.SQL(SQL_statements['geocheck']).format(sql.Identifier(log))]
    d_seq, d_geo_seq, later = add_date(dateOrder, date, query_type)
    sequence.append(d_seq)
    geo_seq.append(d_geo_seq)
    
    # Add SQL for available queries, "filtrate" added later
    if query_type.lower() != 'basic' and query_type in SQL_statements[log].keys():
        sequence.append(sql.SQL(SQL_statements[log][query_type]))
        geo_seq.append(sql.SQL(SQL_statements[log][query_type]))
    # HTTP status
    elif log == 'access' and query_type.endswith('xx'):
        lohi = (int(f'{query_type[0]}00'), int(f'{query_type[0]}99'))
        sequence.append(sql.SQL('AND status BETWEEN {} AND {}').format(lohi[0], lohi[1]))
        geo_seq.append(sql.SQL('AND status BETWEEN {} AND {}').format(lohi[0], lohi[1]))
    # Known Devices
    elif log == 'access' and query_type == 'known devices':
        kd = cur.execute('SELECT knowndevices FROM settings').fetchall()[0][0]
        if kd == None:
            return False, (f'❖ specify Known Devices in report settings ❖', sequence), None   
        sequence.append(sql.SQL('AND tech = ANY({})').format([kd]))
        geo_seq.append(sql.SQL('AND tech = ANY({})').format([kd]))
    # Error - IP version
    elif log == 'error' and query_type.startswith('ip'):
        return False, (f'❖ coming soon to theatres near you! ❖', sequence), None   
    # Error - Log Level
    elif log == 'error' and query_type.startswith('level: '):
        sequence.append(sql.SQL('AND level={}').format(query_type.split(' ')[1]))
        geo_seq.append(sql.SQL('AND level={}').format(query_type.split(' ')[1]))
    # fail2ban - Filter
    elif log == 'fail2ban' and query_type.startswith('filter: '):
        sequence.append(sql.SQL('AND filter={}').format(query_type.split(' ')[1]))  
        geo_seq.append(sql.SQL('AND filter={}').format(query_type.split(' ')[1]))  
    # fail2ban - Ignores (use with Home / Known Devices)
    elif log == 'fail2ban' and query_type == 'ignores':
        sequence.append(sql.SQL('AND action={}').format('Ignore'))
        geo_seq.append(sql.SQL('AND action={}').format('Ignore'))
    
    # additional filters: home/outside, IP search, location search after geocheck
    if log == 'access' and query_type == 'filtrate': # home always False for filtrate
        sequence.append(sql.SQL('AND home={}').format(False))
        geo_seq.append(sql.SQL('AND home={}').format(False))   
    elif log == 'access' and query_type == 'ignorable': # home always True for ignorable
        sequence.append(sql.SQL('AND home={}').format(True))
        geo_seq.append(sql.SQL('AND home={}').format(True))        
    elif homeFilter != None:
        sequence.append(sql.SQL('AND home={}').format(homeFilter))
        geo_seq.append(sql.SQL('AND home={}').format(homeFilter))
    # IP search
    if options[2]:
        sequence.append(sql.SQL('AND ip={}').format(options[2]))
        try:
            cur.execute("SELECT pg_typeof(%s::inet);", (options[2],))
        except:
            return False, (f'❖ Invalid IP address ❖', sequence), None   
        geo_seq.append(sql.SQL('AND ip={}').format(options[2]))
   
   # filtrate add to end, exclude banned IPs from within the week
    if log == 'access' and query_type =='filtrate':
        kd = cur.execute('SELECT knowndevices FROM settings').fetchall()[0][0]
        ban_SQL = [sql.SQL('SELECT DISTINCT(ip) FROM "fail2ban"'), d_seq, 
                   sql.SQL("AND action='Ban'")]
        ban_SQL = ' '.join([val.as_string(cur) for val in ban_SQL])
        banned = cur.execute(ban_SQL).fetchall()
        banned = [val[0] for val in banned] 
        if kd == None: # IP not in banned IPs from timespan
            sequence.append(sql.SQL('AND ip!= ALL({})').format([banned]))
            geo_seq.append(sql.SQL('AND ip!= ALL({})').format([banned]))
        else: # exclude Known Devices, if specified
            sequence.append(sql.SQL('AND tech!= ALL({}) AND ip!= ALL({})').format([kd], [banned]))
            geo_seq.append(sql.SQL('AND tech!= ALL({}) AND ip!= ALL({})').format([kd], [banned]))

    # geocheck, add location info if applicable
    geo_seq.append(sql.SQL('LIMIT {}').format(rows))
    geocheck = cur.execute(' '.join([val.as_string(cur) for val in geo_seq])).fetchall()
    if geocheck != []:
        sequence.insert(1, sql.SQL('LEFT JOIN {} ON {}.{} = {}.{}').format(sql.Identifier('geoinfo'), 
                    sql.Identifier(log), sql.Identifier('geo'), 
                    sql.Identifier('geoinfo'), sql.Identifier('id')))
        cols+=['id','coords','city','country']
    
    # enable location search if geoinfo exists and it's specified
    if (options[0] or options[1]) and geocheck == []:
        return False, ('❖ No location data to search within query ❖', sequence), None
    elif options[0] and options[1]:
        sequence.append(sql.SQL('AND country={} AND city={}').format(options[0], options[1]))
    elif options[0]:
        sequence.append(sql.SQL('AND country={}').format(options[0]))
    elif options[1]:
        sequence.append(sql.SQL('AND city={}').format(options[1]))

    check_seq = copy(sequence)
    check_seq[0] = sql.SQL('SELECT COUNT(date) FROM {}').format(sql.Identifier(log))
    sequence.append(later)
    sequence.append(sql.SQL('LIMIT {}').format(rows))

    return sequence, cols, check_seq