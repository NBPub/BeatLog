from flask import (
    Blueprint, render_template, request, current_app#, redirect, url_for
)
from datetime import datetime, timedelta
from psycopg import sql
from .db_pool import pool
from .ops_data import vacuum_tables, geo_noIP_check
from .ops_geo import null_assessment, modify_geo, geo_table_build, geo_clean, geo_map,\
                    location_bar_chart, top10_bar_chart, location_fill

bp = Blueprint('geography', __name__, url_prefix='/geo')
@bp.route("/", methods = ['GET','POST'])
def geography():
    alert = result =  None
    if 'vacuum' in request.form:
        alert = vacuum_tables(['geoinfo'])    
    with pool.connection() as conn:
        cur = conn.cursor()    
        if request.method == 'POST':
            if 'lookup' in request.form:
                current_app.logger.info('looking up locations . . .')
                alert, result = location_fill(conn, cur)         
            else:
                if 'Update' in request.form:
                    new = [request.form['city'], request.form['country']]
                    alert = modify_geo(conn, cur, 'mod', request.form['Update'], new)
                if 'Delete' in request.form:
                    alert = modify_geo(conn, cur, 'del', request.form['Delete'], None)            
        
        # geoinfo table, unnamed locaations. if geoinfo populated
        places, blanks, no_country, no_city, either = null_assessment(cur)
        if places == 0:  
            return render_template('geo.html', places=places)
        geo_table, IPs = geo_table_build(cur, {'no_names':"country IS NULL OR city IS NULL"}, True)         
    return render_template('geo.html', places=places, blanks=blanks, geo_table=geo_table,
                           IPs=IPs, no_country=no_country, no_city=no_city, alert=alert, result=result)   

@bp.route("/map/", methods = ['GET','POST'])
def geography_map():
    with pool.connection() as conn:
        cur = conn.cursor()
        # nixtip only for button press
        nixtip = True if request.form and 'nixtip' in request.form else False
        # byIP: switch / existing / setting
        if request.form and 'switch' in request.form: 
            byIP = True if request.form['switch'] == 'True' else False
        elif request.form and 'existing_byIP' in request.form: 
            byIP = True if request.form['existing_byIP'] == 'True' else False
        else:
            byIP = cur.execute('SELECT mapcount FROM settings').fetchone()[0]
            
        if request.method == 'GET': # load settings for GET
            duration = cur.execute('SELECT mapdays FROM settings').fetchone() # Recent Map
            duration = timedelta(days=3) if not duration else timedelta(days=duration[0])                                
            stop = datetime.now()
            begin = datetime.now() - duration
        else: # time bounds from form for POST
            stop = datetime.fromisoformat(request.form['end'])
            begin = datetime.fromisoformat(request.form['start'])            
        geomap = geo_map(cur, begin, stop, byIP, nixtip)      
    return render_template('geo_map.html', geomap=geomap, begin=begin, stop=stop, byIP=byIP, nixtip=nixtip)

@bp.route("/assess/", methods = ['GET','POST'])
def geography_assess():
    geo_table = IPs = alert = chart = None
    with pool.connection() as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            # geo tables
            if 'country-select' in request.form:
                geo_table, IPs = geo_table_build(cur, {'country_select':request.form['country-select']}, True)                  
            elif 'count-select' in request.form:
                SQL = '''SELECT  country FROM (SELECT DISTINCT country, COUNT(*)
FROM "geoinfo" GROUP BY country ORDER BY count DESC) "tmp" WHERE count=%s GROUP BY country'''
                countries = [val[0] for val in cur.execute(SQL, (request.form['count-select'],)).fetchall()]
                geo_table, IPs = geo_table_build(cur,{'count_select':countries}, True)                              
            elif 'inspect' in request.form:
                no_IP_where = 'id NOT IN (SELECT DISTINCT geo FROM (SELECT DISTINCT geo FROM error WHERE geo IS NOT NULL UNION ALL \
SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL) "tmp") ORDER by country, city'
                geo_table, IPs = geo_table_build(cur, {'no_IPs':no_IP_where}, False)      
                if not geo_table:
                    alert = ('All locations have associated IPs','warning')                  
            # bar charts
            elif 'barchart' in request.form:
                if request.form['barchart'] == 'country_locs':
                    chart = location_bar_chart(cur, False)
                elif request.form['barchart'] == 'city_locs':
                    chart = location_bar_chart(cur, True) 
                elif request.form['barchart'] == 'country_hits':
                    chart = top10_bar_chart(cur, False, False) 
                elif request.form['barchart'] == 'country_IP':
                    chart = top10_bar_chart(cur, False, True)                         
                elif request.form['barchart'] == 'city_hits':
                    chart = top10_bar_chart(cur, True, False) 
                else:
                    chart = top10_bar_chart(cur, True, True) 
            # modifications
            elif 'Update' in request.form:
                new = [request.form['city'], request.form['country']]
                alert = modify_geo(conn, cur, 'mod', request.form['Update'], new)
            elif 'Delete' in request.form:
                alert = modify_geo(conn, cur, 'del', request.form['Delete'], None)
            elif 'clean_cache' in request.form:
                alert = geo_clean(conn, cur)                
        SQL = '''SELECT * FROM (SELECT DISTINCT country, COUNT(*) "cities" 
FROM "geoinfo" GROUP BY country ORDER BY cities DESC) "tmp" WHERE cities > 4'''
        bigs = cur.execute(SQL).fetchall()       
        SQL = '''SELECT  COUNT(*), cities FROM (SELECT DISTINCT country, COUNT(*) "cities" 
FROM "geoinfo" GROUP BY country ORDER BY cities DESC) "tmp" WHERE cities < 5 GROUP BY tmp.cities 
ORDER BY cities DESC'''
        littles = cur.execute(SQL) .fetchall()
        no_IP = geo_noIP_check(cur)
        _, _, _, _, noname = null_assessment(cur)
        print(noname)
    return render_template('geo_details.html',bigs=bigs, littles=littles, no_IP=no_IP,
                           geo_table=geo_table, IPs=IPs, alert=alert, chart=chart, noname=noname)