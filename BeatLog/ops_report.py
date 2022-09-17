def table_build(data, columns, timerows):
    if data == [] or len(data[0])!=len(columns):
        return None    
    head = [f'<th scope="col">{column}</th>' for column in columns]
    rows = []   
    last_date = data[0][0].day if timerows else None
    for val in data:
        if timerows:
            if val[0].day != last_date:
                rows.append(f'<tr class="table-primary" height="20px"><th scope="row"> </th>{"<td> </td>"*len(val[1:])}</tr>')
            last_date = val[0].day
        tds = [f'<td>{td}</td>' for td in val[1:]]
        rows.append(f'''
<tr>
  <th scope="row">{val[0]}</th>{"".join(tds)}
</tr>''')
    table = f'<thead><tr>{"".join(head)}</tr></thead>\n<tbody>{"".join(rows)}</tbody>'
    return table, len(data)

def chart_build(name, fancy_name, data_options, data, y_axis, x_axis, x_label):
    tooltip = '\ntoolTip: {shared: true},\n' if len(data) > 0 else ''
    axis_defaults = {'titleFontSize':24, 'lineThickness':4, 'tickThickness':4,\
                     'gridThickness':4  }
    light = '"PapayaWhip"'
    dark = '"PeachPuff"'
    for val in ['gridColor', 'labelFontColor']:
        axis_defaults[val] = light
    for val in ['lineColor', 'tickColor', 'titleFontColor', 'tickColor' ]:
        axis_defaults[val] = dark
    for key,val in axis_defaults.items():
        if key not in y_axis.keys():
            y_axis[key] = val
        if key not in x_axis.keys():
            x_axis[key] = val
    y_axis = ','.join([f'{key}:{val}' for key,val in y_axis.items()])
    x_axis = ','.join([f'{key}:{val}' for key,val in x_axis.items()])
     
    data_strings = []
    for i,dataset in enumerate(data):
        option_string = ','.join([f'{key}:{val}' for key,val in data_options[i].items()])
        data_string = ','.join([f'{{ {x_label}:{key}, y:{val} }}' for key,val in data[i].items()])
        data_strings.append(f'{option_string},\ndataPoints: [{data_string}]')   
    data_string = f'data: [{{{"},{".join(data_strings)}}}]'
    del data_strings, option_string
    chart_string = f'''
var chart = new CanvasJS.Chart("{name}", {{theme: "dark1", exportEnabled:true,
	title:{{text: "{fancy_name}", fontColor: "PapayaWhip",}},
    {tooltip}
    axisY:{{
        {y_axis}}},
    axisX:{{
        {x_axis}}},   
    {data_string}}});
chart.render();
        '''
    chart = (name, chart_string)
    return chart

def frequent_table(conn, cur, data, time_select, geocheck):
    if data == []:
        return None
    times = f'''SELECT MIN(date),MAX(date), MAX(date) - MIN(date) "duration" 
FROM "access" WHERE ip='<IP>' AND home=False{time_select}'''
    fails = f'''SELECT date_trunc('second', date) FROM "fail2ban" 
WHERE ip='<IP>' AND action='Ban' AND home=False{time_select}LIMIT 1'''
    table = []
    for val in data:
        SQL = times.replace('<IP>',str(val[0]))
        start, stop, dur = cur.execute(SQL).fetchone()
        SQL = fails.replace('<IP>',str(val[0]))
        bantime = cur.execute(SQL).fetchone()
        bantime = bantime[0] if bantime else bantime
        if geocheck == 0:
            table.append((str(val[0]), val[1], dur, start, stop, bantime))  
        else:
            table.append((str(val[0]), val[1], val[2], dur, start, stop, bantime))       
    cols = ['IP', 'Hits', 'Location', 'Duration', 'Start', 'Stop', 'Ban Time']
    cols.remove('Location') if geocheck == 0 else cols
    table = table_build(table, cols, False)   
    return table

def top10_table(conn, cur, KD_spec, KD_options, time_select, geocheck):
    # Data
    columns = ['KB', 'Date','IP','HTTP/x','Method','Status','Location','URL','Tech']
    if geocheck == 0:
        SQL = f'''SELECT bytes/1000::float4 "kb", date, ip, http/10::float4 "http", method, 
status, CONCAT(referrer, URL) "URL", tech FROM "access" WHERE home=False{time_select} 
ORDER BY bytes DESC LIMIT 10'''        
        columns.remove('Location')
    else:
        SQL = f'''SELECT bytes/1000::float4 "kb", date, ip, http/10::float4 "http", method, 
    status, CONCAT(city,', ', country) "location", CONCAT(referrer, URL) "URL", tech
    FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False{time_select} 
    ORDER BY bytes DESC LIMIT 10'''  

    if KD_options[2]:
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}'))
        tenDataX = table_build(cur.fetchall(), columns, False)
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'))
        tenDataX_kd = table_build(cur.fetchall(), columns, False) 
    else:
        cur.execute(SQL)
        tenDataX = table_build(cur.fetchall(), columns, False)
        tenDataX_kd = None
    tenDataX = tenDataX[0] if tenDataX else tenDataX
    tenDataX_kd = tenDataX_kd[0] if tenDataX_kd else tenDataX_kd

    # RefURL, User-Agent
    SQL1 = f'''SELECT COUNT(*), CONCAT(referrer, URL) "URL" 
FROM "access" WHERE home=False{time_select} 
GROUP BY "URL" ORDER BY count DESC LIMIT 10'''
    SQL2 = f'''SELECT COUNT(*), tech FROM "access" WHERE home=False{time_select} 
GROUP BY tech ORDER BY count DESC LIMIT 10'''

    if KD_options[3]:
        cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec}'))
        tenRefURL = table_build(cur.fetchall(), ['Hits','RefURL'], False)
        cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'))
        tenRefURL_kd = table_build(cur.fetchall(), ['Hits','RefURL'], False)
        
        cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec}'))
        tenTech = table_build(cur.fetchall(), ['Hits','User-Agent'], False) 
        cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'))
        tenTech_kd = table_build(cur.fetchall(), ['Hits','User-Agent'], False) 
    else:
        cur.execute(SQL1)
        tenRefURL = table_build(cur.fetchall(), ['Hits','RefURL'], False)
        tenRefURL_kd = None 
        
        cur.execute(SQL2)
        tenTech = table_build(cur.fetchall(), ['Hits','User-Agent'], False) 
        tenTech_kd = None          
    tenRefURL = tenRefURL[0] if tenRefURL else tenRefURL
    tenRefURL_kd = tenRefURL_kd[0] if tenRefURL_kd else tenRefURL_kd
    tenTech = tenTech[0] if tenTech else tenTech
    tenTech_kd = tenTech_kd[0] if tenTech_kd else tenTech_kd  

    # Location Table
    if geocheck == 0:
        tenCountry = tenCountry_kd = tenCity = tenCity_kd = None
    else:       
        if not cur.execute('SELECT locationtable FROM settings').fetchone()[0]:
            col = "Hits"
            SQL1 = f'''SELECT COUNT(*), country FROM "access"
        INNER JOIN "geoinfo" on access.geo = geoinfo.id
        WHERE home=False{time_select}    
        GROUP BY country ORDER BY count DESC LIMIT 10'''   
            SQL2 = f'''SELECT COUNT(*), CONCAT(city,', ', country) FROM "access"
        INNER JOIN "geoinfo" on access.geo = geoinfo.id
        WHERE home=False{time_select}    
        GROUP BY city, country ORDER BY count DESC LIMIT 10'''
        else:
            col = "Visitors"
            SQL1 = f'''SELECT COUNT(*), country FROM (
        SELECT country,ip FROM "access"
        INNER JOIN "geoinfo" on access.geo = geoinfo.id
        WHERE home=False{time_select} GROUP BY country, ip)
        "tmp" GROUP BY country ORDER BY count DESC LIMIT 10'''    
            SQL2 = f'''SELECT COUNT(*), location FROM (
        SELECT CONCAT(city,', ', country) "location", ip FROM "access"
        INNER JOIN "geoinfo" on access.geo = geoinfo.id
        WHERE home=False{time_select} GROUP BY location, ip)
        "tmp" GROUP BY location ORDER BY count DESC LIMIT 10'''   
        
        if KD_options[4]:
            cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec}'))
            tenCountry = table_build(cur.fetchall(), [col,'Country'], False) 
            cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'))
            tenCountry_kd = table_build(cur.fetchall(), [col,'Country'], False)       
            cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec}'))
            tenCity = table_build(cur.fetchall(), [col,'City'], False) 
            cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'))
            tenCity_kd = table_build(cur.fetchall(), [col,'City'], False) 
        else:
            cur.execute(SQL1)
            tenCountry = table_build(cur.fetchall(), [col,'Country'], False)
            tenCountry_kd = None        
            cur.execute(SQL2)
            tenCity = table_build(cur.fetchall(), [col,'City'], False) 
            tenCity_kd = None           
        tenCountry = tenCountry[0] if tenCountry else tenCountry
        tenCountry_kd = tenCountry_kd[0] if tenCountry_kd else tenCountry_kd
        tenCity = tenCity[0] if tenCity else tenCity
        tenCity_kd = tenCity_kd[0] if tenCity_kd else tenCity_kd      

    return [tenDataX, tenDataX_kd, tenRefURL, tenRefURL_kd, tenTech, tenTech_kd,
           tenCountry, tenCountry_kd, tenCity, tenCity_kd]

def report_build(conn, cur, time_select, report_days):
    # Read Settings other than duration
    cur.execute('SELECT homeignores,knowndevices,locationtable FROM settings')
    ignorable_spec, KD_spec, LocTabCount = cur.fetchone()    
    if KD_spec:
        KD_options = cur.execute('SELECT kd_visit,kd_frequent,kd_data,kd_refURL,kd_loc FROM settings').fetchone()
        KD_spec = f'{KD_spec} AND '
    else:
        KD_options = (False,)*5
        KD_spec = ''       
    ignorable_spec = f' AND {ignorable_spec}' if ignorable_spec else ''
        
    # Top Level Summary, total / unique hits
    home_summary = []
    out_summary = []
    logs = ['access', 'error', 'unauthorized']
    SQL_list = [f'SELECT COUNT(date) FROM "log" WHERE home=True{time_select}',
        f'SELECT COUNT(DISTINCT ip) FROM "log" WHERE home=True{time_select}']   
    for SQL in SQL_list:
        for log in logs:
            # total for access,error,unauthorized. then unique for access,error,unauthorized
            SQL2 = SQL.replace('"log"', f'"{log}"')
            home_summary.append(cur.execute(SQL2).fetchone()[0])
            SQL2 = SQL2.replace('home=True','home=False')
            out_summary.append(cur.execute(SQL2).fetchone()[0]) 
    del SQL_list  
    
    # home IP
    homeIP = cur.execute(f'SELECT ip FROM "homeip"{time_select.replace("AND","WHERE",1)}').fetchall()
    # home Devices
    SQL = f'''SELECT COUNT(*),tech FROM "access"
WHERE home=True{time_select} GROUP BY tech ORDER BY count desc'''
    homeDevices = table_build(cur.execute(SQL).fetchall(), ['Count','User-Agent'],False)   
    
    # home Table, days, total hits, error ~ unuathorized, HTTP/1.x ~ 4xx
    home_table = {}
    SQL = f'''SELECT date_trunc('day', date) "day", COUNT(*) AS count 
    FROM "log" WHERE home=True{time_select} GROUP BY day ORDER BY day'''
    for log in logs:
        SQL2 = SQL.replace('"log"', f'"{log}"')
        home_table[log] = {val[0]:val[1] for val in cur.execute(SQL2).fetchall()}
    SQL = f'''SELECT date_trunc('day', date) "day", COUNT(*) AS count FROM "access" 
WHERE home=True AND status BETWEEN 399 AND 500{time_select} GROUP BY day ORDER BY day'''        
    home_table['4xx'] = {val[0]:val[1] for val in cur.execute(SQL).fetchall()}
    SQL = SQL.replace('AND status BETWEEN 399 AND 500', 'AND http<20')    
    home_table['HTTP/1.x'] = {val[0]:val[1] for val in cur.execute(SQL).fetchall()}
    
    for key in home_table: # fill in 0's
        for day in report_days:
            if day not in home_table[key]:
                home_table[key][day] = 0
    
    # Bar Charts (home/outside Status and Methods)
    SQL = f'''SELECT status, COUNT(*) FROM "access"
WHERE home=True{time_select} GROUP BY status ORDER BY status'''    
    homeStatus = {f'"{val[0]}"': val[1] for val in cur.execute(SQL).fetchall()}
    y_axis = {'title':'"Home Hits"', 'logarithmic':'true'}
    x_axis = {'title':'"Status Code"', 'gridThickness':0}    
    homeStatus = chart_build('homeStatusChart', 'HTTP Status Codes', [{'type': '"column"'}],\
                                   [homeStatus], y_axis, x_axis, 'label')
    SQL2 = SQL.replace('home=True','home=False')
    outStatus = {f'"{val[0]}"': val[1] for val in cur.execute(SQL2).fetchall()}
    
    SQL = SQL.replace('status', 'method')
    homeMethod = {f'"{val[0]}"': val[1] for val in cur.execute(SQL).fetchall()}
    x_axis = {'title':'"Method"', 'gridThickness':0}    
    homeMethod = chart_build('homeMethodChart', 'HTTP Request Methods', [{'type': '"column"'}],\
                                   [homeMethod], y_axis, x_axis, 'label')
    SQL2 = SQL.replace('home=True','home=False')
    outMethod = {f'"{val[0]}"': val[1] for val in cur.execute(SQL2).fetchall()}
    
    # home / fail2ban ignores
    SQL = f'''SELECT  DISTINCT date_trunc('second', fail2ban.date) "time", filter,
http/10::float4 "http",method, status, bytes, CONCAT(referrer, URL) "URL", tech
FROM "fail2ban" INNER JOIN "access" on date_trunc('second',fail2ban.date) = access.date
WHERE access.home=True AND fail2ban.home=True AND fail2ban.action='Ignore'
{ignorable_spec}{time_select.replace("AND date ", "AND fail2ban.date ")} ORDER BY time'''   
    homef2b = table_build(cur.execute(SQL).fetchall(), ['Date', 'Filter','http','Method',\
                                    'Status', 'bytes','Ref+URL','Tech'], True)
        
    # action count bar graph
    # outside Unique IP
    SQL = f'''SELECT day, COUNT(*) FROM (
SELECT DISTINCT ip, date_trunc('day', date) "day"
FROM "access" WHERE home=False{time_select}) "tmp" GROUP BY day'''       
    if KD_options[0]:         
        raw_visitors = {val[0]:val[1] for val in cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}')).fetchall()}    
    else:      
        raw_visitors = {val[0]:val[1] for val in cur.execute(SQL).fetchall()}     
    # add in unique IPs from error and unauthorized log. could use JOIN within SQL
    for log in logs[1:]:
        cur.execute(SQL.replace('\nFROM "access" ',f'\nFROM "{log}" '))
        for val in cur.fetchall():
            if val[0] in raw_visitors:
                raw_visitors[val[0]] += val[1]
    visitors = {f'new Date({key.year},{key.month-1},{key.day})':val for key,val in raw_visitors.items()}               
    # fail2ban Found / Ban / Ignore
    SQL = f'''SELECT date_trunc('day', date) "day", action,  COUNT(*)
FROM "fail2ban" WHERE action IN ('Found','Ban', 'Ignore'){time_select}
GROUP BY day, action'''       
    finds = {}
    bans = {}
    ignores = {}
    for val in cur.execute(SQL).fetchall():
        if val[1] == 'Found':
            finds[f'new Date({val[0].year},{val[0].month-1},{val[0].day})'] = val[2]
        elif val[1] == 'Ban':
            bans[f'new Date({val[0].year},{val[0].month-1},{val[0].day})'] = val[2]
        elif val[1] == 'Ignore':
            ignores[f'new Date({val[0].year},{val[0].month-1},{val[0].day})'] = val[2]            
    ignorable = {f'new Date({day.year},{day.month-1},{day.day})': 
                 home_table['4xx'][day]+home_table['HTTP/1.x'][day] for day in report_days}
    OptionSettings = {'Finds': 'LightSkyBlue', 'Bans': 'PaleGreen', 'Visitors': 'PaleVioletRed', 
                      'Ignores': 'LightSalmon','Ignorable': 'MediumOrchid'}
    chart_options = []
    for key,val in OptionSettings.items():     
        chart_options.append({'type': '"column"', 'showInLegend': 'true',
                              'name':f'"{key}"', 'color':f'"{val}"'})
    y_axis = {'title':'"Hits"', 'gridThickness':1}
    x_axis = {'title':'"Day"', 'gridThickness':0, 'lineThickness':1, 'valueFormatString': '"MMM DD"',\
              'intervalType':'"day"', 'interval':1}       
    actionCounts = chart_build('actionCountChart', 'Daily Action Counts', chart_options,\
                                   [finds,bans,visitors,ignores,ignorable], y_axis, x_axis, 'x')    
    del finds, bans, visitors, ignores, ignorable, OptionSettings
    
    # Outside Daily Line Graph
    SQL = f'''SELECT day, COUNT(*) FROM (
SELECT date_trunc('day', date) "day", COUNT(*) AS count FROM "access"
WHERE home=False{time_select} GROUP BY day, ip ORDER BY day) "tmp" GROUP BY day'''  
    OutLine_unique = {val[0]: val[1] for val in cur.execute(SQL).fetchall()}
    SQL = SQL[SQL.find('(\nS')+2:SQL.find(') "tmp"')].replace(', ip ',' ')
    OutLine_total = {val[0]: val[1] for val in cur.execute(SQL).fetchall()}
    SQL = SQL.replace('access','error')
    OutLine_error = {val[0]: val[1] for val in cur.execute(SQL).fetchall()}
    SQL = SQL.replace('error','unauthorized')
    OutLine_unauth = {val[0]: val[1] for val in cur.execute(SQL).fetchall()}
    
    for val in report_days:
        OutLine_unique[val] = 0 if val not in OutLine_unique.keys() else OutLine_unique[val]
        OutLine_total[val] = 0 if val not in OutLine_total.keys() else OutLine_total[val]
        if OutLine_error != {}:
            OutLine_error[val] = 0 if val not in OutLine_error.keys() else OutLine_error[val]
        if  OutLine_unauth != {}:
            OutLine_unauth[val] = 0 if val not in OutLine_unauth.keys() else OutLine_unauth[val]

    OutLine_unique = {f'new Date({val[0].year},{val[0].month-1},{val[0].day})': val[1] for val in sorted(OutLine_unique.items())}
    OutLine_total = {f'new Date({val[0].year},{val[0].month-1},{val[0].day})': val[1] for val in sorted(OutLine_total.items())}
    OutLine_error = {f'new Date({val[0].year},{val[0].month-1},{val[0].day})': val[1] for val in sorted(OutLine_error.items())}
    OutLine_unauth = {f'new Date({val[0].year},{val[0].month-1},{val[0].day})': val[1] for val in sorted(OutLine_unauth.items())}

    chart_options = [{'type': '"stepLine"', 'showInLegend': 'true','name':'"Access - Total"', 'markerSize':20, 'lineThickness': 5},
                     {'type': '"stepLine"', 'showInLegend': 'true','name':'"Access - Unique"', 'markerSize':20, 'color':'"BlueViolet"', 'lineThickness': 5},
                     {'type': '"line"', 'showInLegend': 'true','name':'"Error"', 'markerSize':20, 'color':'"Tomato"', 'lineThickness': 3},
                     {'type': '"line"', 'showInLegend': 'true','name':'"Unauthorized"', 'markerSize':20, 'color':'"YellowGreen"', 'lineThickness': 3}]
    y_axis = {'title':'"Outside Hits"', 'gridThickness':1}
    x_axis = {'title':'"Date"', 'gridThickness':1, 'valueFormatString': '"MMM DD"',\
              'intervalType':'"day"', 'interval':1, 'lineThickness':1}    
    outDaily = chart_build('outsideDailyChart', 'Daily Visits', chart_options,\
                                   [OutLine_total, OutLine_unique, 
                                    OutLine_error, OutLine_unauth],
                                    y_axis, x_axis, 'x')  
    del OutLine_total, OutLine_unique, OutLine_error, OutLine_unauth   
    
    # Bar Charts, data gathered above
    y_axis = {'title':'"Outside Hits"'}
    x_axis = {'title':'"Method"', 'gridThickness':0}    
    outMethod = chart_build('outsideMethodChart', 'HTTP Request Methods', [{'type': '"column"'}],\
                                   [outMethod], y_axis, x_axis, 'label')
    x_axis = {'title':'"Status Code"', 'gridThickness':0}   
    outStatus = chart_build('outsideStatusChart', 'HTTP Status Codes', [{'type': '"column"'}],\
                                   [outStatus], y_axis, x_axis, 'label')
    
    # Visit distribution of outside IPs
    SQL = f'''SELECT hits, COUNT(*) FROM
(SELECT ip, COUNT(*) "hits" FROM "log" WHERE home=False{time_select}
GROUP BY ip ORDER BY hits) "tmp" GROUP BY hits ORDER BY hits'''   
    outHitsIP = []
    chart_options = []   
    if not KD_options[0]:
        for log in logs: 
            outHitsIP.append({val[0]: val[1] for val in cur.execute(SQL.replace('log',log)).fetchall()})
            chart_options.append({'type': '"column"', 'showInLegend': 'true','name':f'"{log.capitalize()}"'})
    else:
        for log in logs:
            if log == 'access':
                SQL2 = SQL.replace('WHERE',f'WHERE {KD_spec}')
                outHitsIP.append({val[0]: val[1] for val in cur.execute(SQL2.replace('log',log)).fetchall()})
            else:
                outHitsIP.append({val[0]: val[1] for val in cur.execute(SQL.replace('log',log)).fetchall()})
            chart_options.append({'type': '"column"', 'showInLegend': 'true','name':f'"{log.capitalize()}"'})                  
    y_axis = {'title':'"Outside IPs"', 'gridThickness':1, 'lineThickness':1}
    max_hits = max(outHitsIP[0].keys()) if outHitsIP[0].keys() else 5
    if max_hits < 100:    
        x_axis = {'title':'"Hits"', 'gridThickness':0, 'lineThickness':1, 'interval':max_hits//5}
    else:
        x_axis = {'title':'"Hits"', 'gridThickness':0, 'lineThickness':1, 'logarithmic':'true'}
    outHitsIP = chart_build('outsideHitsIP', 'Hit Counts by Log', chart_options,\
                                   outHitsIP, y_axis, x_axis, 'x')
            
    # frequent visitors, IPs with more than 4 hits + location
    geocheck = cur.execute(f"SELECT COUNT(geo) FROM access WHERE geo IS NOT NULL AND home=False{time_select}").fetchone()[0]
    if geocheck == 0:
        SQL = f'''SELECT ip,  COUNT(ip) FROM "access" WHERE home=False{time_select} 
GROUP BY ip HAVING COUNT(ip) > 4 ORDER BY COUNT(ip) DESC'''          
    else:
        SQL = f'''SELECT ip,  COUNT(ip), CONCAT(city,', ', country) "location"
FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False{time_select} 
GROUP BY ip,location HAVING COUNT(ip) > 4 ORDER BY COUNT(ip) DESC'''       
    if KD_options[1]: 
        freqIPs_access = cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}')).fetchall()
        freqIPs_known = cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}')).fetchall()
    else:
        freqIPs_access = cur.execute(SQL).fetchall()
        freqIPs_known = []
    freqIPs_error = cur.execute(SQL.replace('access','error')).fetchall()
 
    freqIPs_access = frequent_table(conn, cur, freqIPs_access, time_select, geocheck)
    freqIPs_error = frequent_table(conn, cur, freqIPs_error, time_select, geocheck)
    freqIPs_known = frequent_table(conn, cur, freqIPs_known, time_select, geocheck)

    # top 10 data transfers, RefURLs, city/country, entry methods
    top10s = top10_table(conn, cur, KD_spec, KD_options, time_select, geocheck)
    
    # filtrate for access, error
    if geocheck == 0:
        SQL = f'''SELECT date,ip,method,http,status,bytes, CONCAT(referrer,URL) "URL", tech 
    FROM "access" WHERE home=False{time_select} AND ip NOT IN 
    (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban'{time_select}) ORDER BY date'''
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}')) 
        AccessFiltrate = table_build(cur.fetchall(), ['Date','IP','Method','HTTP/x',\
                                                             'Status', 'bytes',\
                                                             'URL', 'Tech'], True)         
    else:
        SQL = f'''SELECT date,ip,method,http,status,bytes, CONCAT(city, ', ', country) "location",
    CONCAT(referrer,URL) "URL", tech  FROM "access" INNER JOIN "geoinfo" ON access.geo=geoinfo.id 
    WHERE home=False{time_select} AND ip NOT IN 
    (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban'{time_select}) ORDER BY date'''
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}')) 
        AccessFiltrate = table_build(cur.fetchall(), ['Date','IP','Method','HTTP/x',\
                                                             'Status', 'bytes','Location',\
                                                             'URL', 'Tech'], True)        
    geocheck = cur.execute(f"SELECT COUNT(geo) FROM error WHERE geo IS NOT NULL AND home=False{time_select}").fetchone()[0]
    if geocheck == 0:
        SQL = f'''SELECT date,level, message FROM "error" WHERE home=False{time_select} 
AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban'{time_select}) ORDER BY date'''    
        ErrorFiltrate = table_build(cur.execute(SQL).fetchall(), 
                               ['Date','IP','Level','Message'], True) 
    else:
        SQL = f'''SELECT date,ip,CONCAT(city, ', ', country) "location", level, message
    FROM "error" INNER JOIN "geoinfo" ON error.geo=geoinfo.id WHERE home=False{time_select}
    AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban'{time_select})
    ORDER BY date'''    
        ErrorFiltrate = table_build(cur.execute(SQL).fetchall(), 
                               ['Date','IP','Location','Level','Message'], True)       
    
    # Fail2Ban Charts, Filter: Finds(Total/Unique), Bans(Total/Unique)
    SQL = f'''SELECT action, filter, COUNT(*) FROM "fail2ban" WHERE action IN ('Found','Ban') AND home=False{time_select}
GROUP BY filter, action ORDER BY action desc, filter'''
    filters = []
    totalFinds = {}
    totalBans = {}
    for val in cur.execute(SQL).fetchall():
        if val[1] not in filters:
            filters.append(val[1])
        if val[0] == 'Found':
            totalFinds[f'"{val[1]}"'] = val[2]
        elif val[0] == 'Ban':
            totalBans[f'"{val[1]}"'] = val[2]
    SQL = f'''SELECT action, filter, COUNT(*) FROM (SELECT 
filter, action,  COUNT(*) FROM "fail2ban" WHERE action IN ('Found','Ban') AND 
home=False{time_select} GROUP BY filter, action, ip ORDER BY action desc, filter ) 
"tmp" GROUP BY filter, action ORDER BY action desc, filter'''
    uniqueFinds = {}
    uniqueBans = {}
    for val in cur.execute(SQL).fetchall():
        if val[0] == 'Found':
            uniqueFinds[f'"{val[1]}"'] = val[2]
        elif val[0] == 'Ban':
            uniqueBans[f'"{val[1]}"'] = val[2]

    OptionSettings = {'Finds': 'CornflowerBlue', 'Finds (IP)': 'LightSkyBlue',\
                      'Bans': 'MediumSpringGreen', 'Bans (IP)': 'Aquamarine'}
    chart_options = []
    for key,val in OptionSettings.items():     
        chart_options.append({'type': '"column"', 'showInLegend': 'true',
                              'name':f'"{key}"', 'color':f'"{val}"'})
    y_axis = {'title':'"Hits"', 'gridThickness':1}
    x_axis = {'title':'""', 'gridThickness':0, 'lineThickness':1}    
    
    f2bFilters = chart_build('f2bFilterChart', 'fail2ban Filters', chart_options,\
                             [totalFinds, uniqueFinds, totalBans, uniqueBans],\
                             y_axis, x_axis, 'label') 
    del totalFinds, uniqueFinds, totalBans, uniqueBans, OptionSettings, chart_options
    
    # Unused Filter Check
    jailFilters = cur.execute("SELECT filters['enabled'] from jail").fetchall()
    jailFilters = jailFilters[0][0] if jailFilters != [] else None
    if jailFilters:
        activeFilters = [val['name'] for val in jailFilters]
        unusedFilters = [val for val in activeFilters if val not in filters]
        f2b_unused = []
        for val in unusedFilters:
            seen = cur.execute(f"SELECT date FROM fail2ban WHERE filter='{val}' ORDER BY DATE desc LIMIT 1").fetchone()
            seen = seen[0] if seen else seen
            f2b_unused.append((val, seen)) 
        f2b_unused = table_build(f2b_unused, ['Filter', 'Last Parsed Log Sighting'], False)
        f2b_unused = f2b_unused[0] if f2b_unused else f2b_unused
    else:
        f2b_unused = None
    
    # Recent Actions 20
    geocheck = cur.execute(f"SELECT COUNT(geo) FROM fail2ban WHERE geo IS NOT NULL AND home=False{time_select}").fetchone()[0]
    if geocheck == 0:
        SQL = f'''SELECT * FROM (SELECT date_trunc('milliseconds',date) "date", ip, action, filter
FROM "fail2ban" WHERE action IN ('Found','Ban', 'Ignore'){time_select}
ORDER BY date desc LIMIT 20) "tmp" ORDER BY date'''    
        f2brecent = table_build(cur.execute(SQL).fetchall(), ['Date', 'IP', 'Action', 'Filter'], True) 
    else:
        SQL = f'''SELECT * FROM (SELECT 
    date_trunc('milliseconds',date) "date", ip, action, filter, CONCAT(city, ', ',country)
    FROM "fail2ban" INNER JOIN "geoinfo" on geoinfo.id=fail2ban.geo
    WHERE action IN ('Found','Ban', 'Ignore'){time_select}
    ORDER BY date desc LIMIT 20) "tmp" ORDER BY date'''    
        f2brecent = table_build(cur.execute(SQL).fetchall(), ['Date', 'IP', 'Action', 'Filter', 'Location'], True)  
    f2brecent = f2brecent[0] if f2brecent else f2brecent
    
    return home_summary, out_summary, homeIP, homeDevices, home_table,\
           homef2b, homeStatus, homeMethod, actionCounts, outStatus, outMethod,\
           freqIPs_access, freqIPs_error, freqIPs_known, top10s, AccessFiltrate,\
           ErrorFiltrate, outHitsIP, outDaily, f2bFilters, f2b_unused, f2brecent

def beat_analyze(conn,cur,IP):   
    try:
        cur.execute("SELECT pg_typeof(%s::inet);", (IP,))
    except:
        return (None, IP)
    
    geocheck = cur.execute("SELECT geo from access WHERE ip=%s AND geo IS NOT NULL ORDER BY date desc LIMIT 10",
                              (IP,)).fetchone()
    # access log
    if geocheck:
        SQL = '''
SELECT date, CONCAT(city, ', ', country) "location", method, http::float4/10 "http", status, bytes/1000 "kb", CONCAT(referrer, URL) "URL", tech
FROM "access" JOIN "geoinfo" ON access.geo = geoinfo.id WHERE ip=%s ORDER BY date desc LIMIT 10'''
        columns = ['Date','Location', 'Method','HTTP','Status','KB','URL','user-agent']
    else:
        SQL = '''SELECT date, method, http::float4/10 "http", status, bytes/1000 "kb", CONCAT(referrer, URL) "URL",
        tech FROM access WHERE ip=%s ORDER BY date desc LIMIT 10''' 
        columns = ['Date','Method','HTTP','Status','KB','URL','user-agent']
    access = cur.execute(SQL, (IP,)).fetchall()
    access = table_build(access, columns, True)    
    access = access[0] if access else None   
        
    # fail2ban
    SQL = "SELECT date_trunc('second', date), filter, action FROM fail2ban WHERE ip=%s ORDER BY date desc LIMIT 10"
    fail2ban = cur.execute(SQL, (IP,)).fetchall()
    fail2ban = table_build(fail2ban, ['Date','Filter', 'Action'], True)
    fail2ban = fail2ban[0] if fail2ban else None

    
    # error
    SQL = "SELECT date, level, message FROM error WHERE ip=%s ORDER BY date desc LIMIT 10"
    error = cur.execute(SQL, (IP,)).fetchall()
    error = table_build(error, ['Date','Level', 'Message'], True)
    error = error[0] if error else None
    
    return ([access, fail2ban, error], IP)