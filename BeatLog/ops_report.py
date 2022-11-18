from psycopg import sql

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

def frequent_table(cur, data, start, end, log, cols, strict_duration):
    if data == []:
        return None
    times_strict = '''SELECT MIN(date),MAX(date), MAX(date) - MIN(date) "duration" 
FROM {} WHERE ip=%(frequenter)s AND home=False AND date BETWEEN %(start)s AND %(end)s'''
    times = '''SELECT MIN(date),MAX(date), MAX(date) - MIN(date) "duration" 
FROM {} WHERE ip=%(frequenter)s AND home=False'''
    fails = '''SELECT DISTINCT date_trunc('second', date) FROM "fail2ban" WHERE ip=%(frequenter)s 
AND action='Ban' AND home=False AND date BETWEEN %(start)s AND %(end)s'''
    
    table = []
    for val in data:
        if strict_duration:
            first, last, dur = cur.execute(sql.SQL(times_strict).format(sql.Identifier(log)),
                               {'frequenter':val[0],'start':start,'end':end}).fetchone()
        else: # don't enforce report time range for known devices
            first, last, dur = cur.execute(sql.SQL(times).format(sql.Identifier(log)),
                               {'frequenter':val[0]}).fetchone()
        bantimes = cur.execute(fails, {'frequenter':val[0],'start':start,'end':end}).fetchall()
        if bantimes == []:
            bantime = '&#9940;'
        elif len(bantimes) == 1:
            bantime = f'<b class="text-success">{bantimes[0][0]}</b>'  
        else:
            bantime = [bantimes[0][0]]
            for ban_date in bantimes[1:]:
                if ban_date[0].date() != bantime[-1].date():
                    bantime.append(ban_date[0])           
            if len(bantime) > 1:
                bantime = f"<b class='bg-success px-2'>{len(bantime)}:</b>  {' &#9889; '.join([str(ban_date) for ban_date in bantime])}"    
            else:
                bantime = f'<b class="text-success">{bantimes[0][0]}</b>' 
        val = list(val)
        val.extend([dur,first,last,bantime])
        table.append(val)
    table = table_build(table, cols, False)
    return table

def top10_table(cur, KD_spec, KD_options, start, end, geocheck, LocTabCount):
    # Data
    columns = ['Data', 'Date','IP','HTTP/x','Method','Status','Location','URL','Tech']
    if geocheck == 0:
        SQL = '''SELECT pg_size_pretty(bytes::bigint), date, ip, http/10::float4 "http", method, 
status, CONCAT(referrer, URL) "URL", tech FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
ORDER BY bytes DESC LIMIT 10'''        
        columns.remove('Location')
    else:
        SQL = '''SELECT pg_size_pretty(bytes::bigint), date, ip, http/10::float4 "http", method, 
status, CONCAT(city,', ', country) "location", CONCAT(referrer, URL) "URL", tech 
FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
ORDER BY bytes DESC LIMIT 10'''  

    if KD_options[2]:
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec}'), {'start':start,'end':end})
        tenDataX = table_build(cur.fetchall(), columns, False)
        cur.execute(SQL.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'), {'start':start,'end':end})
        tenDataX_kd = table_build(cur.fetchall(), columns, False) 
    else:
        cur.execute(SQL, {'start':start,'end':end})
        tenDataX = table_build(cur.fetchall(), columns, False)
        tenDataX_kd = None
    tenDataX = tenDataX[0] if tenDataX else tenDataX
    tenDataX_kd = tenDataX_kd[0] if tenDataX_kd else tenDataX_kd

    # RefURL, User-Agent
    SQL1 = '''SELECT COUNT(URL), CONCAT(referrer, URL) "URL", pg_size_pretty(SUM(bytes)/NULLIF(COUNT(URL),0)) 
FROM "access" WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY "URL" ORDER BY count DESC LIMIT 10'''
    SQL2 = '''SELECT COUNT(tech), tech, pg_size_pretty(SUM(bytes)/NULLIF(COUNT(tech),0)) FROM "access" 
WHERE home=False AND date BETWEEN %(start)s AND %(end)s GROUP BY tech ORDER BY count DESC LIMIT 10'''

    if KD_options[3]:
        cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec}'), {'start':start,'end':end})
        tenRefURL = table_build(cur.fetchall(), ['Hits','RefURL','Avg Data'], False)
        cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'), {'start':start,'end':end})
        tenRefURL_kd = table_build(cur.fetchall(), ['Hits','RefURL','Avg Data'], False)
        
        cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec}'), {'start':start,'end':end})
        tenTech = table_build(cur.fetchall(), ['Hits','User-Agent','Avg Data'], False) 
        cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'), {'start':start,'end':end})
        tenTech_kd = table_build(cur.fetchall(), ['Hits','User-Agent','Avg Data'], False) 
    else:
        cur.execute(SQL1, {'start':start,'end':end})
        tenRefURL = table_build(cur.fetchall(), ['Hits','RefURL','Avg Data'], False)
        tenRefURL_kd = None 
        
        cur.execute(SQL2, {'start':start,'end':end})
        tenTech = table_build(cur.fetchall(), ['Hits','User-Agent','Avg Data'], False) 
        tenTech_kd = None          
    tenRefURL = tenRefURL[0] if tenRefURL else tenRefURL
    tenRefURL_kd = tenRefURL_kd[0] if tenRefURL_kd else tenRefURL_kd
    tenTech = tenTech[0] if tenTech else tenTech
    tenTech_kd = tenTech_kd[0] if tenTech_kd else tenTech_kd  

    # Location Table
    if geocheck == 0:
        tenCountry = tenCountry_kd = tenCity = tenCity_kd = None
    else:       
        if not LocTabCount:
            col = "Hits"
            SQL1 = '''SELECT COUNT(country), country, pg_size_pretty(sum(bytes)/NULLIF(COUNT(country),0)) FROM "access" INNER JOIN "geoinfo" 
on access.geo = geoinfo.id WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY country ORDER BY count DESC LIMIT 10'''
            SQL2 = '''SELECT COUNT(loc), CONCAT(city,', ', country) "loc", pg_size_pretty(sum(bytes)/COUNT(loc)) FROM "access" 
INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False AND date BETWEEN 
%(start)s AND %(end)s GROUP BY city, country ORDER BY count DESC LIMIT 10'''
        else:
            col = "Visitors"
            SQL1 = '''SELECT COUNT(country), country, pg_size_pretty(sum(bytes)/NULLIF(COUNT(country),0)) FROM 
(SELECT country,ip,bytes FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False AND 
date BETWEEN %(start)s AND %(end)s  GROUP BY country, ip,bytes) "tmp" GROUP BY country ORDER BY count DESC LIMIT 10'''
            SQL2 = '''SELECT COUNT(loc), loc, pg_size_pretty(sum(bytes)/NULLIF(COUNT(loc),0)) FROM 
(SELECT CONCAT(city,', ', country) "loc",ip,bytes FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False 
AND date BETWEEN %(start)s AND %(end)s GROUP BY loc,ip,bytes) "tmp" GROUP BY loc ORDER BY count DESC LIMIT 10'''
        
        if KD_options[4]:
            cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec}'), {'start':start,'end':end}) #
            tenCountry = table_build(cur.fetchall(), [col,'Country','Avg Data'], False) 
            cur.execute(SQL1.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'), {'start':start,'end':end}) #
            tenCountry_kd = table_build(cur.fetchall(), [col,'Country','Avg Data'], False)       
            cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec}'), {'start':start,'end':end}) #
            tenCity = table_build(cur.fetchall(), [col,'City','Avg Data'], False) 
            cur.execute(SQL2.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}'), {'start':start,'end':end}) #
            tenCity_kd = table_build(cur.fetchall(), [col,'City','Avg Data'], False) 
        else:
            cur.execute(SQL1, {'start':start,'end':end})
            tenCountry = table_build(cur.fetchall(), [col,'Country','Avg Data'], False)
            tenCountry_kd = None        
            cur.execute(SQL2, {'start':start,'end':end})
            tenCity = table_build(cur.fetchall(), [col,'City','Avg Data'], False) 
            tenCity_kd = None           
        tenCountry = tenCountry[0] if tenCountry else tenCountry
        tenCountry_kd = tenCountry_kd[0] if tenCountry_kd else tenCountry_kd
        tenCity = tenCity[0] if tenCity else tenCity
        tenCity_kd = tenCity_kd[0] if tenCity_kd else tenCity_kd      

    return [tenDataX, tenDataX_kd, tenRefURL, tenRefURL_kd, tenTech, tenTech_kd,
           tenCountry, tenCountry_kd, tenCity, tenCity_kd]

def report_build(cur, start, end, report_days):
    # Read Settings other than duration
    cur.execute('SELECT homeignores,knowndevices,locationtable FROM settings')
    ignorable_spec, KD_spec, LocTabCount = cur.fetchone()    
    if KD_spec: # Known Device and Home Ignorable, assemble in/out of SQL query for now.
        KD_options = cur.execute('SELECT kd_visit,kd_frequent,kd_data,kd_refURL,kd_loc FROM settings').fetchone()
        KD_spec = sql.SQL(f'{KD_spec} AND ').as_string(cur)
    else:
        KD_options = (False,)*5
        KD_spec = ''       
    ignorable_spec = sql.SQL(f' AND {ignorable_spec}').as_string(cur) if ignorable_spec else ''
        
    # Top Level Summary, total / unique hits
    home_summary = []
    out_summary = []
    logs = ['access', 'error', 'unauthorized']
    SQL_list = ['SELECT COUNT(date) FROM {} WHERE home=%(inside)s AND date BETWEEN %(start)s AND %(end)s',
        'SELECT COUNT(DISTINCT ip) FROM {} WHERE home=%(inside)s AND date BETWEEN %(start)s AND %(end)s']   
    for SQL in SQL_list:
        for log in logs:
            home_summary.append(cur.execute(sql.SQL(SQL).format(sql.Identifier(log)),
                               {'start':start,'end':end,'inside':True}).fetchone()[0])
            out_summary.append(cur.execute(sql.SQL(SQL).format(sql.Identifier(log)),
                               {'start':start,'end':end,'inside':False}).fetchone()[0])
    del SQL_list    
    # home IP
    homeIP = cur.execute('SELECT ip FROM "homeip" WHERE date BETWEEN %(start)s AND %(end)s',
                        {'start':start,'end':end}).fetchall()
    # home Devices
    SQL = '''SELECT COUNT(*),tech, pg_size_pretty(SUM(bytes)/NULLIF(COUNT(*),0)), pg_size_pretty(SUM(bytes)) 
FROM "access" WHERE home=True AND date BETWEEN %(start)s AND %(end)s GROUP BY tech ORDER BY count desc'''
    homeDevices = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(),
                  ['Count','User-Agent', 'Avg Data', 'Total Data'],False)      
    
    # home Table, days, total hits, error ~ unuathorized, HTTP/1.x ~ 4xx
    home_table = {}
    SQL = '''SELECT date_trunc('day', date) "day", COUNT(*) AS count 
FROM {} WHERE home=True AND date BETWEEN %(start)s AND %(end)s GROUP BY day ORDER BY day'''
    for log in logs:
        home_table[log] = {val[0]:val[1] for val in cur.execute(sql.SQL(SQL)\
                          .format(sql.Identifier(log)),{'start':start,'end':end}).fetchall()}
    SQL = '''SELECT date_trunc('day', date) "day", COUNT(*) AS count FROM "access" WHERE home=True 
AND status BETWEEN 400 AND 499 AND date BETWEEN %(start)s AND %(end)s GROUP BY day ORDER BY day'''        
    home_table['4xx'] = {val[0]:val[1] for val in cur.execute(SQL,{'start':start,'end':end}).fetchall()} 
    SQL = SQL.replace('AND status BETWEEN 400 AND 499', 'AND http<20')  
    home_table['HTTP/1.x'] = {val[0]:val[1] for val in cur.execute(SQL,{'start':start,'end':end}).fetchall()}    
    for key in home_table: # fill in 0's
        for day in report_days:
            if day not in home_table[key]:
                home_table[key][day] = 0    
    
    # Bar Charts (home/outside Status and Methods)
    SQL = '''SELECT {field}, COUNT(*) FROM "access" WHERE home=%(inside)s 
AND date BETWEEN %(start)s AND %(end)s GROUP BY {field} ORDER BY {field}'''
    homeStatus = {f'"{val[0]}"': val[1] for val in cur.execute(sql.SQL(SQL)\
                 .format(field=sql.Identifier('status')),{'start':start,'end':end,'inside':True}).fetchall()}
    y_axis = {'title':'"Home Hits"', 'logarithmic':'true'}
    x_axis = {'title':'"Status Code"', 'gridThickness':0}    
    homeStatus = chart_build('homeStatusChart', 'HTTP Status Codes', [{'type': '"column"'}],
                 [homeStatus], y_axis, x_axis, 'label')   
    homeMethod = {f'"{val[0]}"': val[1] for val in cur.execute(sql.SQL(SQL)\
                 .format(field=sql.Identifier('method')),{'start':start,'end':end,'inside':True}).fetchall()}
    x_axis = {'title':'"Method"', 'gridThickness':0}    
    homeMethod = chart_build('homeMethodChart', 'HTTP Request Methods', [{'type': '"column"'}],
                 [homeMethod], y_axis, x_axis, 'label')   
    # Outside, build charts later
    outMethod = {f'"{val[0]}"': val[1] for val in cur.execute(sql.SQL(SQL)\
                .format(field=sql.Identifier('method')),{'start':start,'end':end,'inside':False}).fetchall()}
    outStatus = {f'"{val[0]}"': val[1] for val in cur.execute(sql.SQL(SQL)\
                .format(field=sql.Identifier('status')),{'start':start,'end':end,'inside':False}).fetchall()}               
    
    # home / fail2ban ignores. Day/Filter count and Access Log matches
    SQL = '''SELECT to_char(date_trunc('day', date), 'MM-DD') "day", filter, COUNT(filter) 
FROM fail2ban WHERE action = 'Ignore' AND date BETWEEN %(start)s AND %(end)s GROUP BY filter, day ORDER BY day'''
    homef2b = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(),['Day', 'Filter','Count'], False)[0]
    if homef2b:
        SQL = f'''SELECT  DISTINCT date_trunc('second', fail2ban.date) "time", filter,
http/10::float4 "http",method, status, bytes, CONCAT(referrer, URL) "URL", tech
FROM "fail2ban" INNER JOIN "access" on date_trunc('second',fail2ban.date) = access.date
WHERE access.home=True AND fail2ban.home=True AND fail2ban.action='Ignore'
{ignorable_spec} AND fail2ban.date BETWEEN %(start)s AND %(end)s ORDER BY time'''
        homef2b = (homef2b, table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(),
              ['Date', 'Filter','http','Method','Status', 'bytes','Ref+URL','Tech'], True))
    # action count bar graph
    # outside Unique IP
    SQL = '''SELECT day, COUNT(*) FROM (SELECT DISTINCT ip, date_trunc('day', date) "day" 
FROM {} WHERE home=False AND date BETWEEN %(start)s AND %(end)s) "tmp" GROUP BY day'''       
    if KD_options[0]:         
        raw_visitors = {val[0]:val[1] for val in cur.execute(\
                        sql.SQL(SQL.replace('WHERE',f'WHERE {KD_spec}'))\
                       .format(sql.Identifier('access')),{'start':start,'end':end}).fetchall()}
    else:      
        raw_visitors = {val[0]:val[1] for val in cur.execute(\
                        sql.SQL(SQL).format(sql.Identifier('access')),{'start':start,'end':end}).fetchall()}     
    # add in unique IPs from error and unauthorized log. could use JOIN within SQL
    for log in logs[1:]:
        cur.execute(sql.SQL(SQL).format(sql.Identifier(log)),{'start':start,'end':end})
        for val in cur.fetchall():
            if val[0] in raw_visitors:
                raw_visitors[val[0]] += val[1]
    visitors = {f'new Date({key.year},{key.month-1},{key.day})':val for key,val in raw_visitors.items()}               
    # fail2ban Found / Ban / Ignore
    SQL = '''SELECT date_trunc('day', date) "day", action,  COUNT(*) FROM "fail2ban" WHERE 
action IN ('Found','Ban', 'Ignore') AND date BETWEEN %(start)s AND %(end)s GROUP BY day, action'''       
    finds = {}
    bans = {}
    ignores = {}
    for val in cur.execute(SQL,{'start':start,'end':end}).fetchall():
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
    x_axis = {'title':'"Day"', 'gridThickness':0, 'lineThickness':1, 
              'valueFormatString': '"MMM DD"','intervalType':'"day"', 'interval':1}       
    actionCounts = chart_build('actionCountChart', 'Daily Action Counts', chart_options,
                   [finds,bans,visitors,ignores,ignorable], y_axis, x_axis, 'x')    
    del finds, bans, visitors, ignores, ignorable, OptionSettings
    
    # Outside Daily Line Graph
    SQL = '''SELECT day, COUNT(*) FROM (SELECT date_trunc('day', date) "day", 
COUNT(*) AS count FROM {} WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY day, ip ORDER BY day) "tmp" GROUP BY day'''  
    OutLine_unique = {val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                     .format(sql.Identifier('access')),{'start':start,'end':end}).fetchall()}
    SQL = SQL[SQL.find('(S')+1:SQL.find(') "tmp"')].replace(', ip ',' ')
    OutLine_total = {val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                     .format(sql.Identifier('access')),{'start':start,'end':end}).fetchall()}
    OutLine_error = {val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                     .format(sql.Identifier('error')),{'start':start,'end':end}).fetchall()}
    OutLine_unauth = {val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                     .format(sql.Identifier('unauthorized')),{'start':start,'end':end}).fetchall()}
    
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

    chart_options = [\
{'type': '"stepLine"', 'showInLegend': 'true','name':'"Access - Total"', 'markerSize':20, 'lineThickness': 5},
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
    outMethod = chart_build('outsideMethodChart', 'HTTP Request Methods', 
                [{'type': '"column"'}],[outMethod], y_axis, x_axis, 'label')
    x_axis = {'title':'"Status Code"', 'gridThickness':0}   
    outStatus = chart_build('outsideStatusChart', 'HTTP Status Codes', 
                [{'type': '"column"'}],[outStatus], y_axis, x_axis, 'label')
    
    # Visit distribution of outside IPs
    SQL = '''SELECT hits, COUNT(*) FROM (SELECT ip, COUNT(*) "hits" 
FROM {} WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY ip ORDER BY hits) "tmp" GROUP BY hits ORDER BY hits'''   
    outHitsIP = []
    chart_options = []   
    if not KD_options[0]:
        for log in logs: 
            outHitsIP.append({val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                             .format(sql.Identifier(log)),{'start':start,'end':end}).fetchall()})
            chart_options.append({'type': '"column"', 'showInLegend': 'true','name':f'"{log.capitalize()}"'})
    else:
        for log in logs:
            if log == 'access':
                SQL2 = SQL.replace('WHERE',f'WHERE {KD_spec}')
                outHitsIP.append({val[0]: val[1] for val in cur.execute(sql.SQL(SQL2)\
                                 .format(sql.Identifier(log)),{'start':start,'end':end}).fetchall()})
            else:
                outHitsIP.append({val[0]: val[1] for val in cur.execute(sql.SQL(SQL)\
                                 .format(sql.Identifier(log)),{'start':start,'end':end}).fetchall()})
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
    geocheck = cur.execute(\
"SELECT COUNT(geo) FROM access WHERE geo IS NOT NULL AND home=False AND date between %(start)s and %(end)s",
                          {'start':start,'end':end}).fetchone()[0]
    if geocheck == 0:  
        SQL = '''SELECT ip, COUNT(ip), pg_size_pretty(SUM(bytes)) FROM {table}
 WHERE home=False AND date BETWEEN %(start)s AND %(end)s GROUP BY ip HAVING COUNT(ip) > 4 ORDER BY COUNT(ip) DESC''' 
        cols = ['IP', 'Hits', 'Data', 'Duration', 'Start', 'Stop', 'Ban Time']
    else:
        SQL = '''SELECT ip, COUNT(ip), CONCAT(city,', ', country) "location", pg_size_pretty(SUM(bytes))
FROM {table} INNER JOIN "geoinfo" on {table}.geo = geoinfo.id WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY ip,location HAVING COUNT(ip) > 4 ORDER BY COUNT(ip) DESC'''     
        cols = ['IP', 'Hits', 'Location', 'Data', 'Duration', 'Start', 'Stop', 'Ban Time(s)<br><em class="fw-normal">max 1 per day</em>']
    if KD_options[1]: 
        freqIPs_access = cur.execute(sql.SQL(SQL.replace('WHERE',f'WHERE {KD_spec}')).format(table=sql.Identifier('access')),
                                    {'start':start,'end':end}).fetchall()
        freqIPs_known = cur.execute(sql.SQL(SQL.replace('WHERE',f'WHERE {KD_spec.replace("NOT","")}')).format(table=sql.Identifier('access')),
                                    {'start':start,'end':end}).fetchall()
    else:
        freqIPs_access = cur.execute(sql.SQL(SQL).format(table=sql.Identifier('access')),
                                    {'start':start,'end':end}).fetchall()
        freqIPs_known = []
    freqIPs_error = cur.execute(sql.SQL(SQL.replace(', pg_size_pretty(SUM(bytes))', ''))\
                   .format(table=sql.Identifier('error')),{'start':start,'end':end}).fetchall()
                        
    freqIPs_access = frequent_table(cur, freqIPs_access, start, end, 'access', cols, True)
    freqIPs_known = frequent_table(cur, freqIPs_known, start, end, 'access', cols, False)
    cols.remove('Data')
    freqIPs_error = frequent_table(cur, freqIPs_error, start, end, 'error', cols, True)

    # top 10 data transfers, RefURLs, city/country, entry methods
    top10s = top10_table(cur, KD_spec, KD_options, start, end, geocheck, LocTabCount)
    
    # filtrate for access, error
    if geocheck == 0:
        SQL = f'''SELECT date,ip,method,http/10::float4 "http",status,bytes, CONCAT(referrer,URL) "URL", tech 
FROM "access" WHERE {KD_spec} home=False AND date BETWEEN %(start)s AND %(end)s AND ip NOT IN (SELECT DISTINCT(ip) FROM 
"fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s) ORDER BY date'''
        AccessFiltrate = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                         ['Date','IP','Method','HTTP/x','Status', 'bytes','URL', 'Tech'], True)
    else:
        SQL = f'''SELECT date,ip,method,http/10::float4 "http",status,bytes, CONCAT(city, ', ', country) "location", 
CONCAT(referrer,URL) "URL", tech  FROM "access" INNER JOIN "geoinfo" ON access.geo=geoinfo.id 
WHERE {KD_spec} home=False AND date BETWEEN %(start)s AND %(end)s AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" 
WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s) ORDER BY date'''
        AccessFiltrate = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                         ['Date','IP','Method','HTTP/x','Status', 'bytes','Location','URL', 'Tech'], True)
    
    geocheck = cur.execute("SELECT COUNT(geo) FROM error WHERE geo IS NOT NULL AND home=False AND date between %(start)s and %(end)s",
                          {'start':start,'end':end}).fetchone()[0]
    if geocheck == 0:
        SQL = '''SELECT date,level, message FROM "error" WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s) ORDER BY date'''    
        ErrorFiltrate = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                        ['Date','IP','Level','Message'], True) 
    else:
        SQL = '''SELECT date,ip,CONCAT(city, ', ', country) "location", level, message 
FROM "error" INNER JOIN "geoinfo" ON error.geo=geoinfo.id WHERE home=False AND date BETWEEN %(start)s AND %(end)s 
AND ip NOT IN (SELECT DISTINCT(ip) FROM "fail2ban" WHERE action='Ban' AND date BETWEEN %(start)s AND %(end)s) ORDER BY date'''  
        ErrorFiltrate = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                        ['Date','IP','Location','Level','Message'], True)       
    
    # Fail2Ban Charts, Filter: Finds(Total/Unique), Bans(Total/Unique)
    SQL = '''SELECT action, filter, COUNT(*) FROM "fail2ban" WHERE action IN ('Found','Ban') AND home=False 
AND date BETWEEN %(start)s AND %(end)s GROUP BY filter, action ORDER BY action desc, filter'''
    filters = []
    totalFinds = {}
    totalBans = {}
    for val in cur.execute(SQL,{'start':start,'end':end}).fetchall():
        if val[1] not in filters:
            filters.append(val[1])
        if val[0] == 'Found':
            totalFinds[f'"{val[1]}"'] = val[2]
        elif val[0] == 'Ban':
            totalBans[f'"{val[1]}"'] = val[2]
    SQL = '''SELECT action, filter, COUNT(*) FROM (SELECT filter,action,COUNT(*) 
FROM "fail2ban" WHERE action IN ('Found','Ban') AND home=False AND date BETWEEN %(start)s AND %(end)s 
GROUP BY filter, action, ip ORDER BY action desc, filter) "tmp" GROUP BY filter, action ORDER BY action desc, filter'''
    uniqueFinds = {}
    uniqueBans = {}
    for val in cur.execute(SQL,{'start':start,'end':end}).fetchall():
        if val[0] == 'Found':
            uniqueFinds[f'"{val[1]}"'] = val[2]
        elif val[0] == 'Ban':
            uniqueBans[f'"{val[1]}"'] = val[2]

    OptionSettings = {'Finds': 'CornflowerBlue', 'Bans': 'MediumSpringGreen',\
                      'Finds (IP)': 'LightSkyBlue','Bans (IP)': 'Aquamarine'}
    chart_options = []
    for key,val in OptionSettings.items():     
        chart_options.append({'type': '"column"', 'showInLegend': 'true',
                              'name':f'"{key}"', 'color':f'"{val}"'})
    if totalFinds != {} and max(totalFinds.values())/min(totalFinds.values()) > 100:
        y_axis = {'title':'"log Hits"', 'gridThickness':1, 'logarithmic':'true','minimum':0.1}
    else:
        y_axis = {'title':'"Hits"', 'gridThickness':1}
    x_axis = {'title':'""', 'gridThickness':0, 'lineThickness':1}    
    
    # max_hits = max(outHitsIP[0].keys()) if outHitsIP[0].keys() else 5
    
    f2bFilters = chart_build('f2bFilterChart', 'fail2ban Filters', chart_options,\
                             [totalFinds, totalBans, uniqueFinds, uniqueBans],\
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
            seen = cur.execute("SELECT date FROM fail2ban WHERE filter=%s ORDER BY DATE desc LIMIT 1",
                              (val,)).fetchone()
            seen = seen[0] if seen else seen
            f2b_unused.append((val, seen)) 
        f2b_unused = table_build(f2b_unused, ['Filter', 'Last Parsed Log Sighting'], False)
        f2b_unused = f2b_unused[0] if f2b_unused else f2b_unused
    else:
        f2b_unused = None
    
    # Recent Actions 20
    geocheck = cur.execute(\
"SELECT COUNT(geo) FROM fail2ban WHERE geo IS NOT NULL AND home=False AND date between %(start)s and %(end)s",
                          {'start':start,'end':end}).fetchone()[0]
    if geocheck == 0:
        SQL = '''SELECT date_trunc('milliseconds',date) "date", ip, action, filter 
FROM "fail2ban" WHERE action IN ('Found','Ban', 'Ignore') AND date BETWEEN %(start)s AND %(end)s 
ORDER BY date desc LIMIT 20'''    
        f2brecent = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                    ['Date', 'IP', 'Action', 'Filter'], True) 
    else:
        SQL = '''SELECT date_trunc('milliseconds',date) "date", ip, action, filter, CONCAT(city, ', ',country) 
FROM "fail2ban" INNER JOIN "geoinfo" on geoinfo.id=fail2ban.geo WHERE action IN ('Found','Ban', 'Ignore') 
AND date BETWEEN %(start)s AND %(end)s ORDER BY date desc LIMIT 20'''    
        f2brecent = table_build(cur.execute(SQL,{'start':start,'end':end}).fetchall(), 
                    ['Date', 'IP', 'Action', 'Filter', 'Location'], True)  
    f2brecent = f2brecent[0] if f2brecent else f2brecent
    
    return home_summary, out_summary, homeIP, homeDevices, home_table,\
           homef2b, homeStatus, homeMethod, actionCounts, outStatus, outMethod,\
           freqIPs_access, freqIPs_error, freqIPs_known, top10s, AccessFiltrate,\
           ErrorFiltrate, outHitsIP, outDaily, f2bFilters, f2b_unused, f2brecent

def beat_analyze(cur,IP):
    try:
        cur.execute("SELECT pg_typeof(%s::inet);", (IP,))
    except:
        return (None, IP)
    geocheck = cur.execute("SELECT geo from access WHERE ip=%s AND geo IS NOT NULL ORDER BY date desc LIMIT 10",
                          (IP,)).fetchone()
    # access log
    if geocheck:
        SQL = '''SELECT date, CONCAT(city, ', ', country) "location", method, http::float4/10 "http", status, 
pg_size_pretty(bytes::bigint), CONCAT(referrer, URL) "URL", tech FROM "access" JOIN "geoinfo" ON access.geo=geoinfo.id 
WHERE ip=%s ORDER BY date desc LIMIT 10'''
        columns = ['Date','Location', 'Method','HTTP','Status','size','URL','user-agent']
    else:
        SQL = '''SELECT date, method, http::float4/10 "http", status, pg_size_pretty(bytes::bigint), 
CONCAT(referrer, URL) "URL", tech FROM access WHERE ip=%s ORDER BY date desc LIMIT 10''' 
        columns = ['Date','Method','HTTP','Status','size','URL','user-agent']
    access = cur.execute(SQL, (IP,)).fetchall()
    access = table_build(access, columns, True)    
    access = access[0] if access else None          
    # fail2ban
    SQL = "SELECT date_trunc('second', date), filter, action FROM fail2ban WHERE ip=%s ORDER BY date desc LIMIT 10"
    fail2ban = cur.execute(SQL, (IP,)).fetchall()
    fail2ban = table_build(fail2ban, ['Date','Filter', 'Action'], True)
    fail2ban = fail2ban[0] if fail2ban else None

    geocheck = cur.execute("SELECT geo from error WHERE ip=%s AND geo IS NOT NULL ORDER BY date desc LIMIT 10",
                          (IP,)).fetchone()    
    # error
    if geocheck:
        SQL = '''SELECT date,CONCAT(city, ', ', country) "location", level, message
FROM error JOIN "geoinfo" ON error.geo = geoinfo.id WHERE ip=%s ORDER BY date desc LIMIT 10'''
        columns = ['Date','Location','Level','Message']
    else:
        SQL = "SELECT date, level, message FROM error WHERE ip=%s ORDER BY date desc LIMIT 10"
        columns = ['Date','Level', 'Message']
    error = cur.execute(SQL, (IP,)).fetchall()
    error = table_build(error, columns, True)
    error = error[0] if error else None   
    return ([access, fail2ban, error], IP)