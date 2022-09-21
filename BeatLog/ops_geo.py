from .ops_report import chart_build
from math import log10
from pathlib import Path
import geoip2.database # MaxMind DB
import requests
import json
from time import sleep, time

def null_assessment(conn, cur):   
    blanks = cur.execute("SELECT COUNT(id) FROM geoinfo WHERE country IS NULL AND city IS NULL").fetchone()[0]  
    no_country = cur.execute("SELECT COUNT(id) FROM geoinfo WHERE country IS NULL").fetchone()[0]  
    no_city = cur.execute("SELECT COUNT(id) FROM geoinfo WHERE city IS NULL").fetchone()[0]
    return blanks, no_country, no_city

def modify_geo(conn, cur, method, geoID, data):
    with conn.transaction(): 
        if method == 'del':
            cur.execute('DELETE FROM geoinfo WHERE id=%s', (geoID,))
            alert = ('Deleted entry', 'success')    
        if method == 'mod':
            cur.execute('SELECT city, country FROM geoinfo WHERE id=%s', (geoID,))
            old = cur.fetchall()[0]
            for i,val in enumerate(data):
                data[i] = old[i] if val == 'None' else data[i]            
            if old != tuple(data):
                cur.execute('UPDATE geoinfo SET city=%s, country=%s WHERE id=%s', (data[0], data[1], geoID))
                alert = ('Updated entry', 'success')
            else:
                alert = ('No changes detected', 'warning')
    return alert

def geo_table_build(conn, cur, where, IPcount):   
    SQL = f'''SELECT id, coords[1]/1E4::float4 "lat", coords[2]/1E4::float4 "lon", 
CONCAT('https://www.openstreetmap.org/#map=14/',coords[1]/1E4::float4,'/',coords[2]/1E4::float4) "OSM",
CONCAT('https://www.google.com/maps/@',coords[1]/1E4::float4,',',coords[2]/1E4::float4,',13z') "Google",
city, country FROM geoinfo WHERE {where}'''   
    geo_table = cur.execute(SQL).fetchall()  
    if geo_table != []:
        SQL ='''SELECT SUM(count) from ((SELECT COUNT(DISTINCT ip) from access WHERE geo=%s)
UNION ALL(SELECT COUNT(DISTINCT ip) from error WHERE geo=%s)) as "tmp"'''
        if IPcount:
            IPs = {}
            for val in geo_table:               
                IPs[val[0]] = int(cur.execute(SQL, (val[0],val[0])).fetchone()[0])
        else:
            IPs = None
    else:
        geo_table = None
        IPs = None       
    return geo_table, IPs

def geo_clean(conn, cur):
    SQL = '''SELECT id FROM geoinfo WHERE id NOT IN 
(SELECT DISTINCT geo FROM (SELECT DISTINCT geo FROM error WHERE geo IS NOT NULL
UNION ALL SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL) "tmp")'''
    cleanIDs = [str(val[0]) for val in cur.execute(SQL).fetchall()]
    if cleanIDs != []:
        cleaning = len(cleanIDs)
        cleanIDs = f'({",".join(cleanIDs)})'
        with conn.transaction():   
            cur.execute(f'DELETE FROM geoinfo WHERE id IN {cleanIDs}')
        return (f'{cleaning} locations removed', 'success')
    else:
        return ('All locations have associated IPs, none removed', 'warning')

def geo_map_table(data, col):
    columns = ['Location', col, 'Latitude', 'Longitude']    
    head = [f'<th scope="col">{column}</th>' for column in columns]
    rows = []   
    for val in data:
        tds = [f'<td>{td}</td>' for td in val[1:]]
        rows.append(f'''
<tr>
  <th class="text-info" scope="row" data-lat="{val[2]}"" data-lon="{val[3]}">
  {val[0]}
  </th>{"".join(tds)}
</tr>''')
    table = f'<thead><tr>{"".join(head)}</tr></thead>\n<tbody>{"".join(rows)}</tbody>'
    return table

def geo_map(conn, cur, timerange, byIP, nixtip):
    if not byIP:
        SQL = f'''SELECT CONCAT(city,', ', country) "location", COUNT(*), 
    coords[1]/1E4::float4 "lat", coords[2]/1E4::float4 "lon" FROM "access"
    INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False {timerange}
    GROUP BY location, coords ORDER BY count DESC'''
        data = cur.execute(SQL).fetchall()
        col = "Hits"
    else:
        SQL = f'''SELECT location, COUNT(*), lat, lon FROM (
SELECT CONCAT(city,', ', country) "location", ip, 
coords[1]/1E4::float4 "lat", coords[2]/1E4::float4 "lon" FROM "access"
INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False {timerange}
GROUP BY location, ip, coords) "tmp" GROUP BY location, lat, lon ORDER BY count desc'''
        data = cur.execute(SQL).fetchall()  
        col = "Visitors"

    if data == []:
        return None
    table = geo_map_table(data, col)
    if len(data) == 1: # origin point, set to place with highest count
        top = f'[{data[0][2]},{data[0][3]}], 2'
    else:
        top = '[0,0],2'       
    counts = []
    for val in data: # assess distribution, assign radius
        counts.append(val[1])
    pts = []
    for location, count, lat, lon in data:
        if nixtip:
            pts.append(f'''
var circle = L.circleMarker([{lat},{lon}], {{
fillOpacity: 0.2, color: 'BlueViolet', radius: {round(8*log10(count)+2,2)}}}).addTo(map);''')
        else:
            pts.append(f'''
var circle = L.circleMarker([{lat},{lon}], {{
    fillOpacity: 0.2, color: 'BlueViolet', radius: {round(8*log10(count)+2,2)}}}).addTo(map)
    .bindTooltip("<b>{count}</b><br>{location}");''')   
    chart = f'''
var map = L.map('map').setView({top});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 9, minZoom: 2, attribution: '© OpenStreetMap'}}).addTo(map);
L.control.scale().addTo(map);{"".join(pts)}'''
    return (len(data), chart, table)      

def location_bar_chart(conn,cur):
    data = cur.execute('SELECT country, COUNT(*) FROM geoinfo GROUP BY country ORDER BY count').fetchall()
    if data == []:
        return None
    data = {f'"{val[0]}"':val[1] for val in data}
    y_axis = {'title':'"Locations (unique coordinates)"', 'labelFontSize':12, 'gridThickness':1}
    x_axis = {'title':'"Country"', 'gridThickness':0, 'labelFontSize':12, 'interval':1}     
    chart = chart_build('LocationBarChart', '',[{'type': '"bar"','axisYType': '"secondary"'}], 
                        [data], y_axis, x_axis, 'label')       
    chart = (chart[0], chart[1].replace('axisY:{\n', 'axisY2:{\n')) # move axis label to top
    return chart

def top10_bar_chart(conn,cur,city,byIP):
    if city:
        location = '''SELECT CONCAT(city,', ', country) "location"'''
    else:
        location = '''SELECT country "location"'''    
    if byIP:
        SQL = f'''SELECT location, COUNT(*) FROM ({location}, ip
FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False
GROUP BY location, ip) "tmp" GROUP BY location ORDER BY count desc LIMIT 10'''
        col = "Visitors"
    else:
        SQL = f'''{location}, COUNT(*)
FROM "access" INNER JOIN "geoinfo" on access.geo = geoinfo.id WHERE home=False
GROUP BY location ORDER BY count DESC LIMIT 10'''
        col = "Hits"    
    data = cur.execute(SQL).fetchall()
    if data == []:
        return None
    if len(data) > 1 and data[0][1] > 10*data[1][1]:
        y_axis = {'title':f'"Log {col}"', 'labelFontSize':12, 'gridThickness':1, 'logarithmic':'true'} 
    else:
        y_axis = {'title':f'"{col}"', 'labelFontSize':12, 'gridThickness':1}        
    data = {f'"{val[0]}"':val[1] for val in data}  
    x_axis = {'title':'"Top 10 Locations"', 'gridThickness':0, 'labelFontSize':14, 'interval':1,
              'labelAngle':15, 'labelFontWeight':'"bold"'}     
    chart = chart_build('top10BarChart', '',[{'type': '"column"'}], 
                        [data], y_axis, x_axis, 'label')   
    return chart        

def location_fill(conn, cur):
    agent = cur.execute('SELECT nominatimagent FROM settings').fetchone()
    if not agent:
        return ('No user agent specified, see Geography Settings','danger')
    else:
        agent = agent[0]
        result = []    
    start = time()
    # Nominatim reverse API (OpenStreetMap), https://nominatim.org/release-docs/develop/api/Reverse/
    base = 'https://nominatim.openstreetmap.org/reverse?'
    headers = {'User-Agent': agent, 'Accept-Language': 'en-US'}
    cities = ['municipality', 'city', 'county', 'state']    
    to_fill = cur.execute('SELECT id,coords, city, country FROM geoinfo WHERE city IS NULL OR country IS NULL').fetchall()
    if to_fill == []:
        return ('No blank locations to lookup', 'warning'), result   
    filled = 0
    for row, coords, old_city, old_country in to_fill:
        with conn.transaction(): 
            try:
                URL = f'{base}lat={coords[0]*1E-4}&lon={coords[1]*1E-4}&format=json&zoom=18'
                data = requests.get(URL,headers=headers)
                data = json.loads(data.content)['address']
                for key in cities:
                    if key in data:
                        city = data[key]
                        break
                    else:
                        city = None
                if data['country'] != old_country or city != old_city:
                    cur.execute('UPDATE geoinfo SET city=%s, country=%s WHERE id=%s', (city,data['country'], row))
                    filled += 1
                result.append(f'({round(coords[0]*1E-4,4)},{round(coords[1]*1E-4,4)}) named {city}, {data["country"]}')
                sleep(1)
            except Exception as e:
                result.append(f'Error -- {e} for ({round(coords[0]*1E-4,4)},{round(coords[1]*1E-4,4)})')
    color = 'success' if filled > 0 else 'danger'
    return (f'{filled} locations named out of {len(to_fill)} in {round(time()-start)} seconds', color), result

def geolocate(conn, cur, log, duration):
    maxmindDB = cur.execute('SELECT maxminddb FROM settings').fetchone()[0]
    if not maxmindDB:
        return
    else:
        maxmindDB = Path(maxmindDB)
        if not maxmindDB.exists() or maxmindDB.suffix != '.mmdb':
            return    
    # gather list of unique IPs
    SQL = f'SELECT DISTINCT ip from {log} WHERE home=False AND date BETWEEN %s AND %s'
    IP_list = cur.execute(SQL, (duration[0],duration[1])).fetchall()
    IP_list = [val[0] for val in IP_list] if IP_list != [] else IP_list
    with geoip2.database.Reader(maxmindDB) as reader:
        for IP in IP_list:            
            try: # find location of IP in database
                response = reader.city(IP)
                # if location has already been catalogued, link IP to key in location table
                coords = [int(response.location.latitude*1E4),int(response.location.longitude*1E4)]
                record = cur.execute('SELECT id from geoinfo WHERE coords=%s', (coords,)).fetchone()  
            except:
                continue 
            with conn.transaction(): 
                try:
                    if not record: # add location to catalog
                        if response.city.names != {}:
                            cur.execute('INSERT INTO geoinfo (coords, city, country) VALUES (%s,%s,%s)',
                                        (coords, response.city.names["en"], response.country.names["en"]))
                        else:
                            cur.execute('INSERT INTO geoinfo (coords) VALUES (%s)', (coords,))
                        record = cur.execute('SELECT id FROM geoinfo WHERE coords=%s', (coords,)).fetchone()[0]
                    else:
                        record = record[0]  
                    # reference catalog in log records
                    SQL = f'UPDATE {log} SET geo=%s WHERE ip=%s AND date BETWEEN %s AND %s AND geo IS NULL'
                    cur.execute(SQL, (record, IP, duration[0], duration[1]))
                except:
                    pass # could do logging here



