from flask import (
    Blueprint, render_template, request, current_app, abort, url_for, json#, redirect, 
)
from datetime import datetime, timedelta
from psycopg import sql
from .db_pool import pool
from .ops_report import table_build
from urllib.request import Request
from urllib.request import urlopen

bp = Blueprint('api_v1', __name__, url_prefix='/api')

@bp.route("/help/", methods = ['GET', 'POST'])
def api_help():
    specs = {val:None for val in ['home','outside','fail2ban', 'geo']}
    if request.method == 'POST' and 'load_example' in request.form:
        spec = request.form['load_example']
        data = json.dumps(json.loads(urlopen(Request(url_for('api_v1.api_v1',_external=True,api_spec=spec))).read().decode('utf-8')),indent=1)
        specs[spec] = data
    return render_template('api_help1.html', specs=specs)
                                                  
@bp.route("/v1/<api_spec>", methods = ['GET'])
def api_v1(api_spec):
    api_spec = api_spec.lower()
    if api_spec not in ['all','home','outside','fail2ban', 'geo']:
        abort(422, description = 'Try "home", "outside", "fail2ban", "geo" or "all".')
    end = datetime.now()
    start = end - timedelta(days=1)
    data=dict(time_bounds=dict(start=start.strftime('%x %X'),end=end.strftime('%x %X')))
    
    with pool.connection() as conn:
        cur = conn.cursor()
        if api_spec == 'home' or api_spec == 'all':
            # Home: Total Hits, IP list, Ignores, Data Transfer   
            home = {}  
            home['total'] = cur.execute('SELECT COUNT(date) FROM "access" WHERE home=True AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            home['IP'] = [str(val[0]) for val in cur.execute('SELECT ip FROM "homeip" WHERE date BETWEEN %s AND %s', (start,end)).fetchall()]
            home['IP_duration'] = cur.execute('SELECT duration FROM "homeip" WHERE date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            home['IP_duration'] = 'All of time' if home['IP_duration'] == None else str(home['IP_duration']).split('.')[0]
            home['ignores'] = cur.execute('''SELECT COUNT(date) FROM "fail2ban" WHERE home=True AND action='ignore' AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
            home['error'] = cur.execute('''SELECT COUNT(date) FROM "error" WHERE home=True AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
            home['data'] = cur.execute('SELECT pg_size_pretty(sum(bytes)) FROM "access" WHERE home=True AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            data['home'] = home
            
        if api_spec == 'outside' or api_spec == 'all':              
            # Outside: Total Hits, Unique IP, Banned IPs, Filtrate IPs, Data Transfer
            out = {}  
            out['total'] = cur.execute('SELECT COUNT(date) FROM "access" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            out['error'] = cur.execute('SELECT COUNT(date) FROM "error" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            out['total'] += out['error']
# COULD MAKE ADD ERROR LOG IPs to this
            out['visitors'] = cur.execute('''SELECT COUNT(ip) FROM (SELECT DISTINCT ip FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s  UNION 
SELECT DISTINCT ip FROM "error" WHERE home=False AND date BETWEEN %(start)s AND %(end)s) "tmp"''', {'start':start,'end':end}).fetchone()[0]
            out['banned'] = cur.execute('''SELECT COUNT(DISTINCT ip) FROM "fail2ban" WHERE home=False AND action='Ban' AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
            # check for Known Devices in settings, exclude from filtrate
            KD = cur.execute('SELECT knowndevices FROM settings').fetchall()[0][0]
            if KD == None:
                out['filtrate'] = cur.execute('''SELECT COUNT(DISTINCT ip) FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
 AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s)''', {'start':start,'end':end}).fetchone()[0]
            else:
                out['known_visitors'] = cur.execute(sql.SQL('SELECT COUNT(DISTINCT ip) FROM "access" WHERE tech=ANY({}) AND home=False AND date BETWEEN %(start)s AND %(end)s')\
                                                    .format([KD]), {'start':start,'end':end}).fetchone()[0]
                out['filtrate'] = cur.execute(sql.SQL('''SELECT COUNT(DISTINCT ip) FROM "access" WHERE tech!=ALL({}) AND home=False AND date BETWEEN %(start)s AND %(end)s 
 AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s)''').format([KD]), {'start':start,'end':end}).fetchone()[0]                
            out['data'] = cur.execute('SELECT pg_size_pretty(sum(bytes)) FROM "access" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
            data['outside'] = out
        if api_spec == 'fail2ban' or api_spec == 'all':
            # fail2ban: IgnoredIPs, Enabled Filters, Ban count by filter, Found count by filter
            f2b = {}   
            check = cur.execute('SELECT date FROM jail').fetchone()
            if check:    
                filters,ig = cur.execute('SELECT filters, ignoreips FROM jail').fetchone()
                f2b['enabled_filters'] = [f['name'] for f in filters['enabled']]
                f2b['ignored_IPs'] = [str(ip) for ip in ig]
                f2b['Finds'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Found' GROUP BY filter", (start,end)).fetchall()}
                f2b['Bans'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Ban' GROUP BY filter", (start,end)).fetchall()}
                f2b['Ignores'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Ignore' GROUP BY filter", (start,end)).fetchall()}
            data['fail2ban'] = f2b
        if api_spec == 'geo' or api_spec == 'all':
            # Geo: Top location hits/visitors, Number of locations
            geo = {}
            check = cur.execute("SELECT COUNT(geo) from access WHERE geo IS NOT NULL AND date BETWEEN %s AND %s", (start,end)).fetchone()
            if check and check[0]>0:   
                cur.execute('''SELECT CONCAT(city,', ', country) "loc", COUNT(city) FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id 
WHERE home=False AND date BETWEEN %s AND %s GROUP BY city, country ORDER BY count DESC LIMIT 1''', (start,end))
                geo['top hits'] = cur.fetchall()[0]
                cur.execute('''SELECT loc, COUNT(loc) FROM (SELECT CONCAT(city,', ', country) "loc",ip FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id 
WHERE home=False AND date BETWEEN %s AND %s GROUP BY loc,ip) "tmp" GROUP BY loc ORDER BY count DESC LIMIT 1''', (start,end))  
                geo['top visitors'] = cur.fetchall()[0]
                cur.execute('''SELECT COUNT(geo) FROM (SELECT DISTINCT geo FROM error WHERE geo IS NOT NULL AND date BETWEEN %(start)s AND %(end)s UNION
SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL AND date BETWEEN %(start)s AND %(end)s) "tmp"''', {'start':start,'end':end})
                geo['locations'] = cur.fetchone()[0]
            data['geo'] = geo
            
    return data
    
@bp.route("/v2/bandwidth/<path:api_spec>", methods = ['GET'])
def api_v2_bandwidth(api_spec):
    # Might need to handle URLs more thorughly, see werkzeug source code for "urls"
    # https://github.com/pallets/werkzeug/blob/main/src/werkzeug/urls.py
    # from werkzeug.urls import url_decode, iri_to_uri
    api_spec = api_spec.split('=')   
    with pool.connection() as conn:
        cur = conn.cursor()
        cols = [col[0] for col in \
        cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s", ('access',))] 
        if len(api_spec) != 2: 
            abort(422, description = f'Invalid specification for api/v2/bandwidth.<br><span class="text-danger">{"=".join(api_spec)}</span>')
        if api_spec[0] not in cols:
            abort(422, description = f'Invalid specification for api/v2/bandwidth. Specified field is not valid.<br><span class="text-danger">{"=".join(api_spec)}</span>')
        b, p = cur.execute(sql.SQL('SELECT SUM(bytes), pg_size_pretty(SUM(bytes)) FROM access WHERE {}=%s').format(sql.Identifier(api_spec[0])), 
             (api_spec[1],)).fetchone()
    
    return {'bandwidth':{'bytes':b,'pretty':p,'query':{'field':api_spec[0],'value':api_spec[1]}}}
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    