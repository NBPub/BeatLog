from pathlib import Path
from datetime import datetime, timedelta
from time import time
from urllib.request import Request
from urllib.request import urlopen
from json import dumps
from psycopg import sql
from .models import LogFile, RegexMethod, Jail

## fail2ban / homeIP    
#
def update_Jail(conn, cur, mod, location, lastcheck):
    if not Path(location).exists():
        return False, (f'Specified jail file not found! Update or delete file location.', 'danger', location)
    
    # check for no modifications or recent check (last half-hour)
    if datetime.fromtimestamp(time()) - lastcheck < timedelta(minutes=30):
        return False, None
    elif datetime.fromtimestamp(Path(location).stat().st_mtime) == mod:
        with conn.transaction(): # no modification, update check time
            cur.execute("UPDATE jail SET lastcheck = %s WHERE location = %s", 
            (datetime.fromtimestamp(time()), location))
        return True, None
    else:
        try:
            new_jail = Jail(location)
            SQL = """UPDATE jail SET date = %s, lastcheck = %s, filters = %s,
                     ignoreIPs = %s WHERE location = %s"""
            with conn.transaction():  # modification detected, update everything
                cur.execute(SQL, (new_jail.modified, datetime.fromtimestamp(time()),
                        dumps(new_jail.enabled_filters), new_jail.ignoreIP, location))
            return True, ('Jail updated', 'info')
        except Exception as e:
            return False, (f'Failed to update jail:\n{str(e)}', 'warning')        
def make_Jail(conn, cur, location, old_jail):
    if not location:
        return False, None
    elif not Path(location).exists():
        return False, ('File not found', 'danger')
    elif location == old_jail:
        return False, ('Location not modified, enter new location to change', 'danger') 
    elif Path(location).suffix != '.local':
        return False, ('Invalid file type, should be "___.local"', 'danger') 
    with conn.transaction(): 
        if old_jail:
            try:
                cur.execute("DELETE FROM jail WHERE location = %s", (old_jail,))  
            except Exception as e:
                return False, (f'Error deleting old jail:\n{str(e)}', 'danger')
        try:
            new_jail = Jail(location)
            SQL = """INSERT INTO jail (date, lastcheck, filters, ignoreIPs, location) 
                     VALUES (%s, %s, %s, %s, %s)"""
            cur.execute(SQL, (new_jail.modified, datetime.fromtimestamp(time()),
                        dumps(new_jail.enabled_filters), new_jail.ignoreIP, location))
            return True, ('Jail established', 'success')
        except Exception as e:
            return False, (f'Failed to create jail:\n{str(e)}', 'danger')        
def delete_Jail(conn,cur, location): 
    try:
        with conn.transaction():
            cur.execute('DELETE FROM jail WHERE location=%s',(location,))
            return True, ('Jail deleted!', 'success')
    except Exception as e:
        return False, (str(e), 'danger')            
def filter_info(cur, name):
    try:
    # Home Ignores
        SQL = '''SELECT COUNT(date) FROM "fail2ban" WHERE filter=%s AND action='Ignore' AND home=True
    AND date BETWEEN date_trunc('minute', now()) - interval '1 day' AND date_trunc('minute', now())'''
        home_ignores = cur.execute(SQL, (name,)).fetchone()[0]
        home_ignores = f'{home_ignores} home ignores'
    # Bans
        SQL = '''SELECT COUNT(DISTINCT ip) FROM "fail2ban" WHERE filter=%s AND action='Ban'
    AND date BETWEEN date_trunc('minute', now()) - interval '1 day' AND date_trunc('minute', now())'''        
        bans = cur.execute(SQL, (name,)).fetchone()[0]
        bans = f'{bans} bans'
    # Finds
        SQL = SQL.replace('Ban','Found')
        finds = cur.execute(SQL, (name,)).fetchone()[0]
        finds = f'{finds} finds'
        return ('success', (finds, bans, home_ignores))  
    except Exception as e:
        return ('danger', ('Error!',str(e)))  
def home_ip(conn, cur):
    try:
        # select last 2
        record = cur.execute("SELECT * FROM homeip ORDER BY date DESC LIMIT 2").fetchall()
        now = datetime.fromtimestamp(time())
        # first time
        if record == []:
            ip = urlopen(Request('https://ident.me')).read().decode('utf8')
            SQL = "INSERT INTO homeip (IP, date) VALUES (%s, %s)"
            cur.execute(SQL, (ip, now))
            duration = None
        else:
            row, last_IP, last_date, duration = record[0]
            check = now - last_date # skip check if less than 30 minutes
            if check > timedelta(minutes=30):       
                # update date and duration
                duration = now - record[1][2] if duration else duration # if it's not first entry (null duration), update duration
                ip = urlopen(Request('https://ident.me')).read().decode('utf8')
                SQL = "UPDATE homeip SET date=%s, duration=%s WHERE row = %s"
                cur.execute(SQL, (now, duration, row))   
                
                if ip != str(last_IP): # if IP has changed, make a new row
                    new_now = datetime.fromtimestamp(time())
                    duration = new_now-now
                    SQL = "INSERT INTO homeip (IP, date, duration) VALUES (%s, %s, %s)"   
                    cur.execute(SQL, (ip, new_now, duration))
            else:
                ip = last_IP
        return (ip, duration)
    except Exception as e:
        return (None, str(e))           

## Regex Methods
# create method, validates with RegexMethod class
def make_RegexMethod(conn,cur, input_name, input_pattern):
    Regex = RegexMethod(input_name, input_pattern)
    if Regex.groups == []:
        return ('No groups specified in regex pattern','danger'), None
    with conn.transaction(): 
        SQL = "INSERT INTO regex_methods (name, pattern, groups) VALUES (%s, %s, %s)"    
        try:
            cur.execute(SQL, (Regex.name, input_pattern, Regex.groups))
            return (f'{Regex.name} created!', 'success'), (Regex.name, Regex.groups, input_pattern)
        except Exception as e:
            return (str(e), 'danger'), None
# populate stuff for main regex page
def gather_RegexMethods(cur):
    regex_groups = cur.execute('SELECT name, groups FROM regex_methods').fetchall()
    regex_groups = {entry[0]: entry[1] for entry in regex_groups if regex_groups}
    regex_patterns = cur.execute('SELECT name, pattern FROM regex_methods').fetchall()
    regex_patterns = {entry[0]: entry[1] for entry in regex_patterns if regex_patterns}  
    regex_logs = {}
    for val in [('time','regex_time'),('primary','regex_1'),('secondary','regex_2')]:
        data = cur.execute(sql.SQL(\
'SELECT regex_methods.name, logfiles.name FROM logfiles INNER JOIN regex_methods ON \
regex_methods.name={}').format(sql.Identifier(val[1]))).fetchall()
        if data != []:
            for regex, log in data:
                if regex in regex_logs: # if method exists, add another entry
                    regex_logs[regex].update({log:val[0]}) 
                else:
                    regex_logs[regex]= {log:val[0]} # method name = {log:role}
    return regex_groups, regex_patterns, regex_logs

## Log Files
# validate log path, check same name as old log for updates
def validate_LogFile(path, old_log):
    if not path.exists():
        return False, ('File not found', 'danger')
    elif path.suffix != '.log':
        return False, ('Invalid filetype. Must be ".log"', 'danger')
    elif path.stem not in ['access','error','unauthorized','fail2ban']:
        return False, ('Unknown log specified: must be NGINX access,error,unauthorized OR fail2ban', 'danger')
    elif old_log and path.stem != old_log:
        return False, (f'Invalid log type, cannot update {old_log} with {path.stem}', 'danger')
    else:
        return LogFile(path), None   
# Create entry in database
def make_LogFile(conn,cur,Log):
    SQL = """INSERT INTO logfiles (location, name, modified, lastParsed) 
VALUES (%s, %s, %s, %s)"""
    # check for existing parsed lines
    parsed = cur.execute(sql.SQL('SELECT date FROM {} ORDER BY date desc LIMIT 1').format(sql.Identifier(Log.name))).fetchone()
    parsed = parsed[0] if parsed else parsed
    if parsed:
        Log.lastParsed = [parsed, None]
    with conn.transaction(): 
        try:
            cur.execute(SQL, (str(Log.location), Log.name, Log.modified, Log.lastParsed))
            return (f'{Log.name} created!', 'success')
        except Exception as e:
            return (str(e), 'danger')
# update location of database entry
def edit_LogFile(conn,cur,Log):
    with conn.transaction():
        try:
            cur.execute("UPDATE logfiles SET location=%s WHERE name=%s", \
                       (str(Log.location), Log.location.stem))
            return ('Log location updated', 'success')
        except Exception as e:
            return (str(e), 'danger')                   
# delete database entry
def delete_LogFile(conn,cur, log):
    with conn.transaction():
        try:
            cur.execute("DELETE FROM logfiles WHERE name=%s", (log,))
            return None
        except Exception as e:
            return (str(e), 'danger')
# check log's date modified and update if changed    
def update_LogFile(conn, cur, log):
    loc, mod = cur.execute('SELECT location,modified FROM logfiles WHERE name=%s', (log,)).fetchone()
    check, message = validate_LogFile(Path(loc), None)
    if not check:
        return {log: message}
    new_mod = datetime.fromtimestamp(Path(loc).stat().st_mtime)
    if mod != new_mod:
        with conn.transaction():
            cur.execute('UPDATE logfiles SET modified=%s WHERE location=%s', (new_mod, loc))
        alert = {log: ('updated', 'success')}
    else:
        alert = {log: ('no changes', 'warning')}
    return alert

def update_all_Logs(conn,cur):
    logs = cur.execute('SELECT name FROM logfiles').fetchall()
    if logs == []:
        return
    alerts = {}
    for log in logs:
        alert = update_LogFile(conn,cur,log[0])
        alerts.update(alert)
    return alerts

# edit log's Regex Methods
def regex_LogFile(conn, cur, regex, log):
    with conn.transaction():
        try:
            SQL = "UPDATE logfiles SET regex_1=%s, regex_2=%s, regex_time=%s WHERE name=%s"        
            cur.execute(SQL, (regex['regex_1'], regex['regex_2'], regex['regex_time'], log))
            return True, ('Methods saved', 'success')
        except Exception as e:
            return False, (str(e), 'danger')