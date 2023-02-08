from flask import (
    Blueprint, render_template, request, current_app, json
)
from datetime import datetime, timedelta
from copy import copy
from psycopg import sql
from .db_pool import pool
from .ops_report import table_build
from .db_query import db_query, add_date

bp = Blueprint('db_view', __name__, url_prefix='/db_view')
# Assemble Query with various options
@bp.route("/", methods = ['GET'])
def db_view():
    def_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
    def_end = datetime.now().strftime('%Y-%m-%dT%H:%M')
    log_buttons = {'access': {'Ignorable':'Home hits matching "Ignorable" specification in settings',
                              'Known Devices': 'User-Agent matching Known Devices specified in settings',
                              'Filtrate': 'Outside hits that were not banned by fail2ban <em>performed in one-week blocks</em>',
                              'Regex2': 'Processed by secondary regex method, no HTTP method or version'}, # add HTTP version + status codes
                   'error':  {'IPv6':'IP version 6', 'IPv4':'IP version 4',
                              'Filtrate': 'Outside hits that were not banned by fail2ban <em>performed in one-week blocks</em>'}, # add levels
                   'fail2ban': {'Ignores':'fail2ban "Ignore" action', 
                                'Match Ignores':'Match <b>f2b</b> ignores to <b>Access</b> log Home hits<br>\
<em>Excess matches likely, use Ignorable to tune results</em>'} # add filters
                   }
    lb2 = {'access':[],'error':[],'fail2ban':[], 'tooltip': 
            {'access':'HTTP version/status code','error': 'Log Level','fail2ban':'f2b Filter'}}

    with pool.connection() as conn:
        cur = conn.cursor()
        # check logs for data, get first / last entry + geo info span
        logs = cur.execute('SELECT Name,lastParsed FROM logfiles ORDER BY name').fetchall() 
        log_info = {}
        for log in logs:
            if log[1][0] == datetime(1,1,1):
                log_info[log[0]] = None      
            else:
                SQL = sql.SQL("SELECT date FROM {} ORDER BY date LIMIT 1").format(sql.Identifier(log[0]))
                first = cur.execute(SQL).fetchone()[0]
                SQL = sql.SQL("SELECT date FROM {} WHERE geo is NOT NULL and home=False ORDER BY date LIMIT 1").format(sql.Identifier(log[0]))
                geofirst = cur.execute(SQL).fetchone()[0]
                SQL = sql.SQL("SELECT date FROM {} WHERE geo is NOT NULL and home=False ORDER BY date DESC LIMIT 1").format(sql.Identifier(log[0]))
                geolast = cur.execute(SQL).fetchone()[0]
                log_info[log[0]] = [first, log[1][0], geofirst, geolast]
                if log[0] == 'fail2ban':
                    more =  cur.execute('SELECT DISTINCT(filter) from fail2ban').fetchall()
                    for val in more:
                        lb2[log[0]].append(f'filter: {val[0]}')
                elif log[0] == 'error':
                    more =  cur.execute('SELECT DISTINCT(level) from error').fetchall()
                    for val in more:
                        lb2[log[0]].append(f'level: {val[0]}')
                elif log[0] == 'access':
                    lb2[log[0]].append('HTTPv2')
                    lb2[log[0]].append('HTTPv1')
                    more =  cur.execute('SELECT DISTINCT(FLOOR(status/100)) from access').fetchall()
                    for val in more:
                        lb2[log[0]].append(f'{int(val[0])}xx')   
        # check = True means no data to query, skip getting country/city lists
        check = [val == None for val in log_info.values()]
        if check == [True,]*len(log_info.keys()):
            check = True
            country_list = []
            city_list = []
        else:
            check = False
            country_list = [val[0] for val in 
                            cur.execute('SELECT DISTINCT(country) from geoinfo ORDER BY country').fetchall()]
            city_list = [val[0] for val in 
                            cur.execute('SELECT DISTINCT(city) from geoinfo ORDER BY city').fetchall()]

    return render_template('data_view.html', log_info=log_info, check=check, log_buttons=log_buttons, lb2=lb2,
                            def_start=def_start, def_end=def_end, country_list=country_list, city_list=city_list)

@bp.route("/result", methods = ['POST'])
def db_view_result():
    next_seq = None
    prev_seq = None    
    bounds = None
    
    form_data = {key:request.form[key] for key in request.form}    
    if 'previous' in request.form and request.form['previous'] != '':
        prev_seq = json.loads(request.form['previous'])
        del form_data['previous']
        
    # Generate SQL options from Query Page
    if request.form['dateOrder'] == 'desc':
        date = datetime.strptime(request.form['end'],'%Y-%m-%dT%H:%M')
    else:
        date = datetime.strptime(request.form['start'],'%Y-%m-%dT%H:%M')
    rows = int(request.form['maxRows'])
    options = [val if val != '' else None for val in [request.form['countryOptions'], \
               request.form['cityOptions'], request.form['IP_search']]]
    if 'countryNULL' in request.form:
        options[0] = 'NULL'
    if 'cityNULL' in request.form:
        options[1] = 'NULL'        
    homeFilter = bool(request.form['homeFilter'] == 'True') if request.form['homeFilter'] != 'all' else None
    log, query_type = request.form['query_log'].split(',')
    
    with pool.connection() as conn:
        cur = conn.cursor()   
        # columns for table display
        cols = [col[0] for col in \
            cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (log,))]          
        # generate SQL, add geo, get check SQL to see if result larger than limit
        sequence, cols, check_seq = db_query(log, query_type, request.form['dateOrder'], date, rows, homeFilter, options, cur, cols)       
                
        if sequence == False: # Error building SQL query, show SQL string, no data
            SQL_r = ' '.join([val.as_string(cur) for val in cols[1]])
            alert = (cols[0], 'danger')
            table = None              
        else: # Perform SQL query, style return into table
            alert = None
            SQL_r = ' '.join([val.as_string(cur) for val in sequence])
            data = cur.execute(SQL_r).fetchall()            
            # clean for geoinfo
            remove = []
            if 'coords' in cols:
                remove = ['geo','id']
                rm_ind = [cols.index(k) for k in remove]
            elif 'geo' in cols:
                remove = ['geo'] 
                rm_ind = [cols.index(k) for k in remove]
            if remove != []:
                olddata = data
                data = []
                for i,val in enumerate(olddata):
                    data.append([olddata[i][k] for k in range(0,len(olddata[i])) if k not in rm_ind])
                _ = [cols.pop(cols.index(k)) for k in remove]
            table = table_build(data, cols, True)
            bounds = [data[0][0].strftime('%x %X'), data[len(data)-1][0].strftime('%x %X')] if table else bounds
            
            # if result > size limit, provide "next" query, and provide current query for return
            total = cur.execute(' '.join([val.as_string(cur) for val in check_seq])).fetchone()[0] 
            if total > rows:
                next_form = copy(form_data)
                next_form['date'] = data[len(data)-1][0].strftime('%Y-%m-%dT%H:%M')                
                next_seq = (total, json.dumps(form_data), next_form)

    return render_template('data_view_result.html', SQL_r=SQL_r, table=table, alert=alert, 
                            next_seq=next_seq, prev_seq=prev_seq, bounds=bounds)