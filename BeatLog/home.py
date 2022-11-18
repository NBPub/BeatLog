from flask import (
    Blueprint, render_template, request, current_app#, redirect, url_for
)
from pathlib import Path
from datetime import datetime, timedelta
from psycopg import sql
from .db_pool import pool, conninfo
from .db import db_startup
from .ops_log import home_ip, update_Jail, make_Jail, delete_Jail,\
                     update_LogFile, filter_info, update_all_Logs
from .ops_data import log_data_cleaning, log_clean_estimate, log_clean_confirmed,\
                      geo_noIP_check, vacuum_tables                      
from .ops_parse import parse_all
from .ops_report import report_build, beat_analyze
from sys import version

bp = Blueprint('home', __name__, url_prefix='/')
@bp.before_app_request
def pool_check(): # function not used for NullConnectionPool
    if pool._closed:
        pool.open() # open on first request
        pool.check() # check to populate pool
    pool.check() # check to clean pool
      
@bp.route("/", methods = ['GET', 'POST'])
@bp.route("/home/", methods = ['GET', 'POST'])
def home():
    alert = {}   
    if request.method == 'POST' and 'vacuum' in request.form: # update log data - garbage collect
        alert[request.form['vacuum']] =  vacuum_tables([request.form['vacuum']])        
    with pool.connection() as conn:
        cur = conn.cursor()
        # Footer Info
        versions = cur.execute('SELECT version();').fetchone()[0].split(' ')[0:2]
        versions.append(version.split(' ')[0])
        
        # check home IP, gather ignoreIPs from f2b jail
        homeIP, duration = home_ip(conn, cur)
        ig = cur.execute('SELECT ignoreips FROM jail').fetchone()
        ig = ig[0] if ig else []
        
        # Check date modified for log(s), update if changed
        if request.method == 'POST' and 'log_check' in request.form:
            if request.form['log_check'] == 'update_all':
                alert = update_all_Logs(conn,cur)
            else:
                alert = update_LogFile(conn, cur, request.form['log_check'])
        # Parse all logs
        elif request.method == 'POST' and 'parse_all' in request.form:
            current_app.logger.info('parsing logs . . .')
            alert = parse_all(conn, cur)
    
        # LogFile information: modified, last parsed, first record, # lines, duration
        logs = cur.execute('SELECT Name,Modified,lastParsed FROM logfiles ORDER BY name').fetchall()            
        log_info = {}
        for log in logs:
            if log[2][0] == datetime(1,1,1):
                log_info[log[0]] = None
            else:
                SQL = sql.SQL("SELECT date FROM {} ORDER BY date LIMIT 1").format(sql.Identifier(log[0]))
                first = cur.execute(SQL).fetchone()[0]
                rows = cur.execute('SELECT reltuples::int AS estimate FROM pg_class WHERE relname = %s',
                                    (log[0],)).fetchone()[0]
                rows = "{:,}".format(rows)
                log_info[log[0]] = f'<b>{rows} records</b><br>Starting <b>{first.strftime("%x")}</b> over \
<b>{(log[2][0] - first).days} days</b>'
    print(logs)  
    print()
    print(log_info)
    return render_template('home.html', homeIP=homeIP, duration=duration, logs=logs, versions=versions,
                            check=datetime(1,1,1), ignoreIPs=ig, alert=alert, log_info=log_info)

@bp.route("/data_cleaning/", methods = ['GET','POST'])
def data_clean():
    alert = estimate = existing = None
    disable = False
    if request.method == 'POST' and 'vacuum' in request.form:
        alert = vacuum_tables(['access','error','fail2ban','unauthorized'])    
    with pool.connection() as conn:
        cur = conn.cursor()
        logs, table = log_data_cleaning(cur) # logs with > 0 rows, table of data
        noIPgeo = geo_noIP_check(cur)
        versions = [cur.execute('SELECT version();').fetchone()[0]]
        versions.append(f'Python - {version}')
                    
        if request.method == 'POST' and 'Estimate' in request.form or 'confirm_delete' in request.form:
            existing = (request.form['log_select'],request.form['start'],
                        request.form['stop'])   
            if 'Estimate' in request.form:
                estimate = log_clean_estimate(cur,existing)                   
                if estimate:
                    estimate = f'{"{:,}".format(estimate)} out of {logs[existing[0]]}\
                                rows, {round(100*estimate/int(logs[existing[0]].replace(",","")),1)}%, \
                                of {existing[0].capitalize()} data would be deleted!'
                    disable = True
                else:
                    alert = ('No records would be deleted', 'warning')                
            elif 'confirm_delete' in request.form:
                alert = log_clean_confirmed(conn,cur, existing)
                if alert[1] == 'success':
                    logs, table = log_data_cleaning(cur) 
                    existing = None                   
    return render_template('data_clean.html', logs=logs, table=table, alert=alert, disable=disable,
                           estimate=estimate, existing=existing, noIPgeo=noIPgeo, versions=versions)

@bp.route("/failed_regex/", methods = ['GET','POST'])
def failed_regex():
    with pool.connection() as conn:
        cur = conn.cursor()
        failed = cur.execute('SELECT log, line FROM failedregex').fetchall()
        if failed != []:
            lines = len(failed)
        else:
            lines = 0
    return render_template('failed_regex.html', lines=lines)

@bp.route("/settings/", methods = ['GET','POST'])
def settings():  
    alert = mm_check = None
    with pool.connection() as conn:
        cur = conn.cursor()     
        old = cur.execute('SELECT * FROM settings').fetchone()  
        if old[9]: # maxmind check, message for None, another for false, date modified for true
            p = Path(old[9])
            mm_check = datetime.fromtimestamp(p.stat().st_mtime).strftime('%x %X') if p.exists() and p.suffix == '.mmdb' else False
    
        oldRep = (old[0], old[1], old[2], old[3], old[4], old[5], old[6], old[7], old[8])
        oldGeo = (old[9], old[10], old[11], old[12])
        
        if request.method == 'POST':
            if 'ReportSet' in request.form: # report settings
                newRep = (int(request.form['ReportDays']), \
                          request.form['HomeIgnore'] if request.form['HomeIgnore'].replace(' ','') !='' else None,
                          request.form['KnownDevices'] if request.form['KnownDevices'].replace(' ','') !='' else None,
                          True if 'KD_1' in request.form else False, True if 'KD_2' in request.form else False, 
                          True if 'KD_3' in request.form else False, True if 'KD_4' in request.form else False, 
                          True if 'KD_5' in request.form else False, True if request.form['LocTab']=='IP' else False)       
                if newRep != oldRep:
                    with conn.transaction():
                        cur.execute('UPDATE settings SET reportdays=%s,homeignores=%s,knowndevices=%s,\
                                      KD_visit=%s,KD_frequent=%s,KD_data=%s,KD_refurl=%s,KD_loc=%s,\
                                      LocationTable=%s WHERE mapdays=%s', (newRep[0], newRep[1], newRep[2],
                                      newRep[3], newRep[4], newRep[5],newRep[6], newRep[7], newRep[8], old[10]))
                    alert = ('Report settings updated', 'success')            
                else:
                    alert = ('No changes detected', 'warning')               
            elif 'GeoSet' in request.form: # geography settings
                newGeo = (request.form['mmdb_loc'] if request.form['mmdb_loc'].replace(' ','') !='' else None, 
                          int(request.form['GeoDays']), True if request.form['MapCount']=='IP' else False,
                          request.form['NominatimAgent'] if request.form['NominatimAgent'].replace(' ','') !='' else None)
                if newGeo != oldGeo:
                    with conn.transaction():
                        cur.execute('UPDATE settings SET maxminddb=%s,mapdays=%s,mapcount=%s,\
                        nominatimagent=%s WHERE reportdays=%s', (newGeo[0], newGeo[1], newGeo[2], newGeo[3], old[0]))
                    if newGeo[0]:
                        p = Path(newGeo[0])
                        mm_check = datetime.fromtimestamp(p.stat().st_mtime).strftime('%x %X') if p.exists() and p.suffix == '.mmdb' else False   
                    else:
                        mm_check = None
                    alert = ('Geography settings updated', 'success')            
                else:
                    alert = ('No changes detected', 'warning')                      
        if alert and alert[1] == 'success':
            old = cur.execute('SELECT * FROM settings').fetchone()   
    return render_template('settings.html', old=old, alert=alert, mm_check=mm_check)   
    
@bp.route("/Beat/", methods = ['POST'])
def Beat():
    with pool.connection() as conn:
        cur = conn.cursor()    
        beatIP = request.form['BeatLog']
        beatIP = beat_analyze(cur, beatIP)
    return render_template('BeatLog.html', beatIP=beatIP)

@bp.route("/report/", methods = ['GET', 'POST'])
def recent_report():
    current_app.logger.info('generating report . . .')
    with pool.connection() as conn:
        cur = conn.cursor()   
        if request.method == 'POST' and 'CustomReport' in request.form:
            end = datetime.strptime(request.form['end'],'%Y-%m-%dT%H:%M')
            start = datetime.strptime(request.form['start'],'%Y-%m-%dT%H:%M')
            duration = (end - start).days                
        else:
            duration = cur.execute('SELECT reportdays FROM settings').fetchone()
            duration = 3 if not duration else duration[0]
            end = datetime.now()
            start = (end - timedelta(days=duration))
        
        end_day = datetime(year=end.year,month=end.month,day=end.day)
        report_days = [end_day]
        i = 1
        while i <= duration:
            report_days.append(end_day - timedelta(days=i))
            i+=1
        del end_day, i
        report_days.sort()
   
        home_summary, out_summary, homeIP, homeDevices, home_table, homef2b,\
        homeStatus, homeMethod, actionCounts, outStatus, outMethod, \
        freqIPs_access, freqIPs_error, freqIPs_known, top10s, AccessFiltrate,\
        ErrorFiltrate, outHitsIP, outDaily, f2bFilters,\
        f2b_unused, f2brecent = report_build(cur, start, end, report_days)   
                     
    return render_template('recent_report.html',duration=duration, start=start, end=end,
                            home_summary=home_summary, out_summary=out_summary, homeIP=homeIP, 
                            homeDevices=homeDevices, report_days=report_days, home_table=home_table, 
                            homeStatus=homeStatus, homeMethod=homeMethod, homef2b=homef2b,
                            outStatus=outStatus, outMethod=outMethod,
                            actionCounts=actionCounts, top10s=top10s,freqIPs_access=freqIPs_access,
                            freqIPs_error=freqIPs_error,freqIPs_known=freqIPs_known,
                            AccessFiltrate=AccessFiltrate, ErrorFiltrate=ErrorFiltrate,
                            outHitsIP=outHitsIP, outDaily=outDaily,
                            f2bFilters=f2bFilters, f2b_unused=f2b_unused, f2brecent=f2brecent)                       

@bp.route("/jail/", methods = ['GET','POST'])
def configure_jail():
    location = message =  None
    made = False
    with pool.connection() as conn:
        cur = conn.cursor()  
        jail = cur.execute('SELECT * FROM jail').fetchone() # location, date modified, last check, filters, ignoredIPs
        homeIP,_ = home_ip(conn, cur)
        if jail:
            location = jail[0]
            made, message = update_Jail(conn, cur, jail[1], location, jail[2]) # returns up to date, updated, or failure message
            if message and len(message) == 3: # file not found
                jail = None
        if request.method == 'POST':
            if 'set_jail' in request.form and 'Location' in request.form:              
                made, message = make_Jail(conn, cur, request.form['Location'], location)  # new location, old location          
            elif 'delete_jail' in request.form and location:
                made,message = delete_Jail(conn,cur,location)                
        if request.method == 'POST' and 'all_activity' in request.form:
            for log in jail[3]['enabled']:
                stats = filter_info(cur, log['name'])
                log['stats'] = stats
            del stats
        elif request.method == 'POST' and 'activity' in request.form:
            stats = filter_info(cur, request.form['activity'])
            for log in jail[3]['enabled']:
                if log['name'] == request.form['activity']:
                    log['stats'] = stats
            del stats        
        if made:
            jail = cur.execute('SELECT * FROM jail').fetchone()    
        if jail and len(jail[3]['enabled']) > 0:
            watch_logs = [val['log'] for val in jail[3]['enabled']]
            watch_logs = set(watch_logs)
        else:
            watch_logs = None              
        ig = cur.execute('SELECT ignoreips FROM jail').fetchone()
        ig = ig[0] if ig else []       
    return render_template('jail.html', jail=jail, message=message, homeIP=homeIP,
                            ignoreIPs=ig, watch_logs=watch_logs)

