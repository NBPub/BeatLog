from psycopg import sql

def summary(start, end, api_spec, cur):
    summary_data = {}
    
    # Home: Total Hits, IP list, Ignores, Data Transfer   
    if api_spec == 'home':       
        summary_data['total'] = cur.execute('SELECT COUNT(date) FROM "access" WHERE home=True AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
        summary_data['IP'] = [str(val[0]) for val in cur.execute('SELECT ip FROM "homeip" WHERE date BETWEEN %s AND %s', (start,end)).fetchall()]
        summary_data['IP_duration'] = cur.execute('SELECT duration FROM "homeip" WHERE date BETWEEN %s AND %s', (start,end)).fetchone()[0]
        summary_data['IP_duration'] = 'All of time' if summary_data['IP_duration'] == None else str(summary_data['IP_duration']).split('.')[0]
        summary_data['ignores'] = cur.execute('''SELECT COUNT(date) FROM "fail2ban" WHERE home=True AND action='ignore' AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
        summary_data['error'] = cur.execute('''SELECT COUNT(date) FROM "error" WHERE home=True AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
        summary_data['data'] = cur.execute('SELECT pg_size_pretty(sum(bytes)) FROM "access" WHERE home=True AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]      
    
    # Outside: Total Hits, Unique IP, Banned IPs, Filtrate IPs, Data Transfer  
    elif api_spec == 'outside':                   
        summary_data['total'] = cur.execute('SELECT COUNT(date) FROM "access" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
        summary_data['error'] = cur.execute('SELECT COUNT(date) FROM "error" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
        summary_data['total'] += summary_data['error']
# ~~~ COULD ADD ERROR LOG IPs to this ~~~
        summary_data['visitors'] = cur.execute('''SELECT COUNT(ip) FROM (SELECT DISTINCT ip FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s  UNION 
SELECT DISTINCT ip FROM "error" WHERE home=False AND date BETWEEN %(start)s AND %(end)s) "tmp"''', {'start':start,'end':end}).fetchone()[0]
        summary_data['banned'] = cur.execute('''SELECT COUNT(DISTINCT ip) FROM "fail2ban" WHERE home=False AND action='Ban' AND date BETWEEN %s AND %s''', (start,end)).fetchone()[0]
        # check for Known Devices in settings, exclude from filtrate
        KD = cur.execute('SELECT knowndevices FROM settings').fetchall()[0][0]
        if KD == None:
            summary_data['filtrate'] = cur.execute('''SELECT COUNT(DISTINCT ip) FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s)''', {'start':start,'end':end}).fetchone()[0]
        else:
            summary_data['known_visitors'] = cur.execute(sql.SQL('SELECT COUNT(DISTINCT ip) FROM "access" WHERE tech=ANY({}) AND home=False AND date BETWEEN %(start)s AND %(end)s')\
                                                .format([KD]), {'start':start,'end':end}).fetchone()[0]
            summary_data['filtrate'] = cur.execute(sql.SQL('''SELECT COUNT(DISTINCT ip) FROM "access" WHERE tech!=ALL({}) AND home=False AND date BETWEEN %(start)s AND %(end)s 
AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s)''').format([KD]), {'start':start,'end':end}).fetchone()[0]                
        summary_data['data'] = cur.execute('SELECT pg_size_pretty(sum(bytes)) FROM "access" WHERE home=False AND date BETWEEN %s AND %s', (start,end)).fetchone()[0]
    
    # fail2ban: IgnoredIPs, Enabled Filters, Ban count by filter, Found count by filter  
    elif api_spec == 'fail2ban':      
        check = cur.execute('SELECT date FROM jail').fetchone()
        if check:    
            filters,ig = cur.execute('SELECT filters, ignoreips FROM jail').fetchone()
            summary_data['enabled_filters'] = [f['name'] for f in filters['enabled']]
            summary_data['ignored_IPs'] = [str(ip) for ip in ig]
            summary_data['Finds'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Found' GROUP BY filter", (start,end)).fetchall()}
            summary_data['Bans'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Ban' GROUP BY filter", (start,end)).fetchall()}
            summary_data['Ignores'] = {val[0]:val[1] for val in cur.execute("SELECT filter, count(filter) FROM fail2ban WHERE date BETWEEN %s AND %s AND action='Ignore' GROUP BY filter", (start,end)).fetchall()}
    
    # Geo: Top location hits/visitors, Number of locations
    elif api_spec == 'geo':        
        check = cur.execute("SELECT COUNT(geo) from access WHERE geo IS NOT NULL AND date BETWEEN %s AND %s", (start,end)).fetchone()
        if check and check[0]>0:   
            cur.execute('''SELECT CONCAT(city,', ', country) "loc", COUNT(city) FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id 
WHERE home=False AND date BETWEEN %s AND %s GROUP BY city, country ORDER BY count DESC LIMIT 1''', (start,end))
            summary_data['top hits'] = cur.fetchall()[0]
            cur.execute('''SELECT loc, COUNT(loc) FROM (SELECT CONCAT(city,', ', country) "loc",ip FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id 
WHERE home=False AND date BETWEEN %s AND %s GROUP BY loc,ip) "tmp" GROUP BY loc ORDER BY count DESC LIMIT 1''', (start,end))  
            summary_data['top visitors'] = cur.fetchall()[0]
            cur.execute('''SELECT COUNT(geo) FROM (SELECT DISTINCT geo FROM error WHERE geo IS NOT NULL AND date BETWEEN %(start)s AND %(end)s UNION
SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL AND date BETWEEN %(start)s AND %(end)s) "tmp"''', {'start':start,'end':end})
            summary_data['locations'] = cur.fetchone()[0]
    return summary_data
    
    
def bandwidth(api_spec, date_spec, cur):    
 
    cols = [col[0] for col in \
    cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s", ('access',))]
    cols.remove('date')
    
    # Invalid FIELD specification
    if api_spec[0] not in cols:
        return f'Invalid specification for api/v2/bandwidth/. . .<span class="text-success mx-3">FIELD=VALUE</span>\
                 <br>Specified field is not valid: <span class="text-danger mx-3 fw-bold">{api_spec[0]}</span>'
    
    # Allow LIKE matches for strings, https://www.postgresql.org/docs/current/functions-matching.html
    if api_spec[0] in ['url','tech','referrer'] and api_spec[1].find('%') != -1:
        joiner = 'LIKE'
        if api_spec[1] == '%': # don't allow "match everything"
            return f'Invalid specification for api/v2/bandwidth/. . . <br>LIKE expression for <span class="text-warning fw-bold">{api_spec[0]}</span>\
                     must contain at least one specific character, not only "<span class="text-danger fw-bold">%</span>"'
    else:
        joiner = '='
    # Capitalize HTTP method (GET/POST/REPORT . . .)
    api_spec[1] = api_spec[1].upper() if api_spec[0].lower() == 'method' else api_spec[1]
    
    # Perform query with/without date bounds. Try/Except to capture invalid data types and ?
    try:
        if not date_spec:        
            # Adjust statement for NULL values
            if api_spec[1].lower() == 'none':
                joiner= 'IS NULL'
                api_spec[1] = None
                byte, pretty, count, pph = cur.execute(sql.SQL(f'''
    SELECT SUM(bytes), pg_size_pretty(SUM(bytes)),COUNT(bytes), pg_size_pretty(SUM(bytes)/COUNT(bytes)) FROM access WHERE {{}} {joiner}''')\
                                           .format(sql.Identifier(api_spec[0]))).fetchone()              
            else:           
                byte, pretty, count, pph = cur.execute(sql.SQL(f'''
    SELECT SUM(bytes), pg_size_pretty(SUM(bytes)),COUNT(bytes), pg_size_pretty(SUM(bytes)/COUNT(bytes)) FROM access WHERE {{}} {joiner} %s''')\
                                           .format(sql.Identifier(api_spec[0])),(api_spec[1],)).fetchone()  
            # query information for return
            query = {'field':api_spec[0],'value':api_spec[1]}
        
        else:
            # Adjust statement for NULL values
            if api_spec[1].lower() == 'none':
                joiner= 'IS NULL'
                api_spec[1] = None
                byte, pretty, count, pph = cur.execute(sql.SQL(f'''
    SELECT SUM(bytes), pg_size_pretty(SUM(bytes)),COUNT(bytes), pg_size_pretty(SUM(bytes)/COUNT(bytes)) FROM access WHERE {{}} {joiner} AND date BETWEEN %s AND %s''')\
                                           .format(sql.Identifier(api_spec[0])), (date_spec[0],date_spec[1])).fetchone()  
            else:
                byte, pretty, count, pph = cur.execute(sql.SQL(f'''
    SELECT SUM(bytes), pg_size_pretty(SUM(bytes)),COUNT(bytes), pg_size_pretty(SUM(bytes)/COUNT(bytes)) FROM access WHERE {{}} {joiner} %s AND date BETWEEN %s AND %s''')\
                                           .format(sql.Identifier(api_spec[0])), (api_spec[1],date_spec[0],date_spec[1])).fetchone()   
            
            query =  {'field':api_spec[0],'value':api_spec[1], 'time_bounds':dict(start=date_spec[0].strftime('%x'), end=date_spec[1].strftime('%x'))} 
    except Exception as e:
        e = str(e).split('\n')[0]
        return f'Invalid specification for api/v2/bandwidth/. . .<br><span class="text-danger">{e}</span>'

    return {'bandwidth':{'bytes':byte,'data':pretty,'hits':count, 'data_per_hit': pph, 'query':query}}
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    