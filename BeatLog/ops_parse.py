from time import time
from datetime import datetime
import re
from pathlib import Path
from psycopg import sql
from .models import RegexMethod
from .ops_log import update_LogFile, home_ip
from .ops_geo import geolocate

def log_homeIP(conn, cur, log):
    # get start date to gather homeIPs
    start = cur.execute(sql.SQL('SELECT date FROM {} WHERE home IS NULL ORDER BY date ASC LIMIT 1').format(sql.Identifier(log))).fetchone()[0]
    # get homeIPs after updating
    _ = home_ip(conn, cur)
    data = cur.execute('SELECT row, ip, date FROM homeip WHERE date > %s ORDER BY date', (start,)).fetchall()    
    with conn.transaction():   
        if len(data) == 1: # one IP forever or for entire range, update everything
            cur.execute(sql.SQL('UPDATE {} SET home=True WHERE home IS NULL AND ip=%s').format(sql.Identifier(log)), 
                       (data[0][1],))
            cur.execute(sql.SQL('UPDATE {} SET home=False WHERE home IS NULL AND ip!=%s').format(sql.Identifier(log)),
                       (data[0][1],))   
        else: # multiple IPs, update sequentially
            for IP_record in data:
                cur.execute(sql.SQL('UPDATE {} SET home=True WHERE home IS NULL AND ip=%s AND date < %s').format(sql.Identifier(log)),
                            (IP_record[1], IP_record[2]))
                cur.execute(sql.SQL('UPDATE {} SET home=False WHERE home IS NULL AND ip!=%s AND date < %s').format(sql.Identifier(log)),
                            (IP_record[1], IP_record[2]))         

def regex_test(cur, log_file, alias): # log file's location, log_name
    location = cur.execute('SELECT location FROM logfiles WHERE name=%s', (log_file,)).fetchone()[0]      
    patterns = {}
    for key,val in alias.items():
        name = cur.execute(sql.SQL('SELECT {} FROM logfiles WHERE name=%s')\
               .format(sql.Identifier(key)), (log_file,)).fetchone()[0] 
        patterns[val] = re.compile(cur.execute('SELECT pattern FROM regex_methods WHERE name=%s',
                       (name,)).fetchone()[0], re.IGNORECASE) if name else name
    result = {}
    # Time Skips 
    if patterns['Time Skip']:
        start = time()
        success = 0
        failed = 0
        with open(location, mode='rt') as file:
            for line in file:
                parsed = re.search(patterns['Time Skip'],line)
                if parsed:
                    success+=1
                else:
                    failed+=1
        result['Time Skip'] = f'{success+failed} lines tested in {round(time()-start)} seconds<br>'
        if success > 0:
            result['Time Skip'] += f'<span class="ms-3 px-2 bg-success text-light">{success} parsed</span><br>'
        if failed > 0:
            result['Time Skip'] += f'<span class="ms-3 px-2 bg-danger text-light">{failed} failed</span>'   
    if patterns['Primary'] and patterns['Secondary']:
        start = time()
        success = 0
        caught = 0
        failed = 0
        with open(location, mode='rt') as file:
            for line in file:
                parsed = re.search(patterns['Primary'],line)
                if parsed:
                    success+=1
                else:
                    parsed = re.search(patterns['Secondary'],line)
                    if parsed:
                        caught+=1
                    else:
                        failed+=1       
        result['Primary'] = f'{sum([success,caught,failed])} lines tested in {round(time()-start)} seconds<br>'
        result['Secondary'] = f'{sum([success,caught,failed])} lines tested in {round(time()-start)} seconds<br>' 
        if success > 0:
            result['Primary'] += f'<span class="ms-3 px-2 bg-success text-light">{success} parsed</span><br>'
        if caught > 0:
            result['Primary'] += f'<span class="ms-3 px-2 bg-danger text-light">{caught} failed</span><br>'
            result['Secondary'] += f'<span class="ms-3 px-2 bg-success text-warning">\
                                    {caught} caught by secondary</span><br>'
        elif caught == 0 and failed == 0:
            result['Secondary'] += f'<span class="ms-3 px-2 bg-success text-light">{caught} searched</span><br>'        
        if failed > 0:
            result['Secondary'] += f'<span class="ms-3 px-2 bg-danger text-light">{failed} failed both methods!</span>'   
    elif patterns['Primary'] or patterns['Secondary']:
        role = 'Primary' if patterns['Primary'] else 'Secondary'
        start = time()
        success = 0
        failed = 0
        with open(location, mode='rt') as file:
            for line in file:
                parsed = re.search(patterns[role],line)
                if parsed:
                    success+=1
                else:
                    failed+=1  
        result[role] = f'{success+failed} lines tested in {round(time()-start)} seconds<br>'
        if success > 0:
            result[role] += f'<span class="ms-3 px-2 bg-success text-light">{success} parsed</span><br>'
        if failed > 0 and log_file != 'fail2ban':
            result[role] += f'<span class="ms-3 px-2 bg-danger text-light">{failed} failed</span>'
        elif failed > 0:
            result[role] += f'<span class="ms-3 px-2 bg-warning text-dark">{failed} irrelevant</span>'   
    return result

# fail2ban  parse
def parsef2b(conn, cur, log):
    # update LogFile, then get info
    _ = update_LogFile(conn, cur, log)    
    loc, lastParsed, mod, regex_1, regex_time = \
    cur.execute("SELECT location, lastparsed, modified, regex_1, regex_time FROM logfiles WHERE name=%s", 
                (log,)).fetchone() 
    if not regex_1:
        return None, ('Add regex methods to log', 'danger'), (lastParsed, mod, regex_1, None, regex_time)
    
    if lastParsed[0] == datetime(1,1,1) or lastParsed[1] != mod:  
        time_format = '%Y-%m-%d %H:%M:%S,%f'
        primary =  RegexMethod('primary', 
                   cur.execute('SELECT pattern FROM regex_methods WHERE name = %s', (regex_1,)).fetchone()[0])
        time_skipper =  RegexMethod('time_skipper', 
                        cur.execute('SELECT pattern FROM regex_methods WHERE name = %s', (regex_time,)).fetchone()[0])  
        SQL = "INSERT INTO fail2ban (date, ip, filter, action) VALUES (%s,%s,%s,%s)" # leave query hard coded due to actionIP split
        failed_lines = []
        record = [0,0,0] # timeskips+ignored, added, failed, append seconds taken at the end
        
        start = time()
        with open(Path(loc), mode='rt') as file, conn.transaction():
            for line in file:
                try:
                    parsed = re.search(time_skipper.pattern, line)
                    if parsed and datetime.strptime(parsed.group(time_skipper.groups[0]), time_format) < lastParsed[0]:
                        record[0]+=1
                        continue                   
                    parsed = re.search(primary.pattern,line)
                    if parsed: # primary regex
                        data = {item: parsed.group(item) for item in primary.groups}
                        if data["level"] in ['INFO','NOTICE']: 
                            if data["actionIP"].split(' ')[0] in ['Found', 'Ban', 'Ignore']:
                                date = datetime.strptime(data["date"], time_format)
                                action = data["actionIP"].split(' ')[0]
                                IP = data["actionIP"].split(' ')[1]
                                cur.execute(SQL, (date, IP, data["filter"], action))                      
                                record[1]+=1
                            else:
                                record[0]+=1
                        else:
                            record[0]+=1
                    else:
                        record[0]+=1
                except:
                    failed_lines.append(line)
                    record[2]+=1

        if record[1] > 0: # update lastParsed, assess homeIPs, add geodata.            
            try: # lastParsed: try saving last read line, if not last saved line
                lastParsed_2 = [datetime.strptime(re.search(time_skipper.pattern, line)\
                                .group(time_skipper.groups[0]), time_format), mod]
            except:
                lastParsed_2 = [cur.execute(sql.SQL('SELECT date FROM {} ORDER BY date DESC LIMIT 1')\
                               .format(sql.Identifier(log))).fetchone()[0], mod]
            with conn.transaction():
                cur.execute('UPDATE logfiles SET lastparsed = %s WHERE name = %s', (lastParsed_2, log))              
            log_homeIP(conn, cur, log) # assess homeIPs for new records                
            geolocate(conn, cur, log, (lastParsed[0], lastParsed_2[0])) # parse geolocations          
            alert = ('Parsing completed', 'success')
        else: # no changes, update date modified
            lastParsed_2 = [lastParsed[0], mod]
            with conn.transaction():
                cur.execute('UPDATE logfiles SET lastparsed = %s WHERE name = %s', (lastParsed_2, log))
            alert = ('No new lines parsed!', 'danger')                           
        if record[2] > 0: # save failed lines
            with conn.transaction():
                SQL = 'INSERT INTO failedregex (line, log) VALUES (%s,%s)'
                for line in failed_lines:
                    cur.execute(SQL, (line, log))
                del failed_lines               
        record.append(round(time()-start))
        return record, alert, (lastParsed_2, mod, regex_1, None, regex_time)
    else:
        return None, ('fail2ban has not changed since last parse', 'warning'), (lastParsed, mod, regex_1, None, regex_time)

def parse(conn, cur, log):
    # update LogFile, then get info
    _ = update_LogFile(conn, cur, log) 
    loc, log, mod, lastParsed, regex_1, regex_2, regex_time = \
    cur.execute('SELECT * FROM logfiles WHERE name=%s', (log,)).fetchone()
    if not regex_1 or not regex_2:
        return None, ('Add regex methods to log', 'danger'), (lastParsed, mod, regex_1, regex_2, regex_time)
    
    if lastParsed[0] == datetime(1,1,1) or lastParsed[1] != mod: # last parsed check, returns on else
        for i,name in enumerate([regex_1, regex_2, regex_time]):
            if name:
                cur.execute('SELECT pattern FROM regex_methods WHERE name = %s', (name,))
                if i == 0:
                    primary = RegexMethod('primary', cur.fetchone()[0])                   
                    SQL_1 = sql.SQL('INSERT INTO {table} ({fields}) VALUES ({values}) ').format(
                           table=sql.Identifier(log),
                           fields=sql.SQL(',').join([sql.Identifier(group.lower()) for group in primary.groups]),
                           values=sql.SQL(',').join([sql.Placeholder()]*len(primary.groups))) 
                elif i == 1:
                    secondary = RegexMethod('secondary', cur.fetchone()[0])
                    SQL_2 = sql.SQL('INSERT INTO {table} ({fields}) VALUES ({values}) ').format(
                           table=sql.Identifier(log),
                           fields=sql.SQL(',').join([sql.Identifier(group.lower()) for group in secondary.groups]),
                           values=sql.SQL(',').join([sql.Placeholder()]*len(secondary.groups))) 
                elif i == 2:
                    time_skipper = RegexMethod('time_skipper', cur.fetchone()[0])     
        record = [0,0,0,0] # timeskips, primary, secondary, failed, operation time(s) appended later
        failed_lines = []
        time_format = '%Y/%m/%d %H:%M:%S' if log == 'error' else '%d/%b/%Y:%H:%M:%S'

        start = time() # begin parsing
        with open(Path(loc), mode='rt') as file, conn.transaction():
            for line in file:
                if regex_time: # time skip
                    parsed = re.search(time_skipper.pattern, line)
                    if parsed and datetime.strptime(parsed.group(time_skipper.groups[0]), time_format) < lastParsed[0]:
                        record[0]+=1
                        continue                
                parsed = re.search(primary.pattern,line)
                if parsed: # primary regex
                    data = {item: parsed.group(item) for item in primary.groups}
                    data["date"] = datetime.strptime(data["date"], time_format)
                    if 'IP' in data.keys() and data["IP"].find('[') + data["IP"].find(']') != -2: # adjust ipv6
                        data["IP"] = data["IP"].replace('[','').replace(']','')
                    if 'http' in data.keys(): # change HTTP version to integer
                        data["http"] = round(float(data["http"])*10) if data["http"] else data["http"]
                    if 'level' in data.keys(): # keep only text for error log level
                        data["level"] = data["level"].replace('[','').replace(']','')
                    cur.execute(SQL_1, tuple(data.values()))
                    record[1]+=1               
                elif regex_2: # secondary regex
                    parsed = re.search(secondary.pattern,line)
                    if parsed:
                        data = {item: parsed.group(item) for item in secondary.groups}
                        data["date"] = datetime.strptime(data["date"], time_format)
                        if 'IP' in data.keys() and data["IP"].find('[') + data["IP"].find(']') != -2:
                            data["IP"] = data["IP"].replace('[','').replace(']','')
                        if 'http' in data.keys():
                            data["http"] = round(float(data["http"])*10) if data["http"] else data["http"]    
                        if 'level' in data.keys():
                            data["level"] = data["level"].replace('[','').replace(']','')
                        cur.execute(SQL_2, tuple(data.values()))
                        record[2]+=1
                else: # failed regex
                    failed_lines.append(line)
                    record[3]+=1
        
        # update lastParsed, assess homeIPs, add geodata       
        if record[1] + record[2] > 0:
            lastParsed_2 = [cur.execute(sql.SQL('SELECT date FROM {} ORDER BY date DESC LIMIT 1')\
                            .format(sql.Identifier(log))).fetchone()[0], mod]   
            with conn.transaction():
                cur.execute('UPDATE logfiles SET lastparsed = %s WHERE name = %s', (lastParsed_2, log))            
            log_homeIP(conn, cur, log)
            geolocate(conn, cur, log, (lastParsed[0], lastParsed_2[0]))            
            alert = ('Parsing completed', 'success')
        else: # no adds, update modified
            lastParsed_2 = [lastParsed[0], mod]
            with conn.transaction():
                cur.execute('UPDATE logfiles SET lastparsed = %s WHERE name = %s', (lastParsed_2, log))
            alert = ('No new lines parsed!', 'danger')
        if record[3] > 0: # save failed lines
            with conn.transaction():
                SQL = 'INSERT INTO failedregex (line, log) VALUES (%s,%s)'
                for line in failed_lines:
                    cur.execute(SQL, (line, log))
                del failed_lines       
        record.append(round(time()-start))   
        return record, alert, (lastParsed_2, mod, regex_1, regex_2, regex_time)
    else:
        return None, (f'{log} has not changed since last parse', 'warning'), (lastParsed, mod, regex_1, regex_2, regex_time)

def parse_all(conn, cur):
        log_files = [name[0] for name in cur.execute('SELECT name FROM logfiles').fetchall()]
        if log_files == []:
            return None
        alerts = {}    
        for log_file in log_files:
            try:
                if log_file == 'fail2ban':
                    record, alert, _ = parsef2b(conn, cur, log_file)
                    if record:
                        alert = (f'{alert[0]}, {record[1]} lines added in {record[3]}s', 'success')
                else:
                    record, alert, _ = parse(conn, cur, log_file)
                    if record:
                        alert = (f'{alert[0]}, {sum(record[1:3])} lines added in {record[4]}s', 'success')
            except Exception as e:
                alert = (str(e), 'danger')
            alerts[log_file] = alert
        return alerts