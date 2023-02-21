from flask import (
    Blueprint, render_template, request, current_app, redirect, url_for
)
from pathlib import Path
from datetime import datetime
from .db_pool import pool
from .ops_log import make_LogFile, make_RegexMethod, edit_LogFile, regex_LogFile,\
                     gather_RegexMethods, validate_LogFile, delete_LogFile
from .ops_parse import regex_test, parse, parsef2b
from .ops_data import populate_regex

bp = Blueprint('logs', __name__, url_prefix='/Logs')    
@bp.route("/add_regex/", methods = ['GET', 'POST'])
def add_regex_method():
    alert = existing = None
    with pool.connection() as conn:
        cur = conn.cursor()
        if request.method == 'POST' and 'populate_methods' in request.form:
            populate_regex(conn, cur)
        regex_groups, regex_patterns, regex_logs= gather_RegexMethods(cur)  
        logs = [name[0] for name in cur.execute('SELECT name FROM logfiles').fetchall()]        
        # Form submitted - delete method
        if request.method == 'POST':
            if 'delete_method' in request.form:
                existing = (request.form['delete_method'], regex_patterns[request.form['delete_method']])
                with conn.transaction():
                    try: # delete existing method
                        cur.execute('DELETE FROM regex_methods WHERE name=%s', (existing[0],))
                        if existing[0] in regex_logs:
                            affected = [f'<li>{val.capitalize()} method for {key} log removed</li>' for key,val in regex_logs[existing[0]].items()]
                            alert = (f'<b>{existing[0]} deleted</b><ul class="ms-3">{"".join(affected)}</ul>', 'warning')
                        else:
                            alert = (f'{existing[0]} deleted', 'warning')
                        del regex_groups[existing[0]]
                    except Exception as e:
                        existing = None
                        alert = (str(e), 'danger')               
        # add new regex method
            elif 'Add_Regex_Method' in request.form:
                existing = (request.form['name'], request.form['pattern'])
                if regex_patterns and existing[0] in regex_patterns.keys():
                    alert = ('Regex Method name must be unique.', 'danger')
                else:           
                    alert, new_Reg = make_RegexMethod(conn, cur, existing[0],existing[1])            
                    if alert[1] == 'success':
                        regex_groups[new_Reg[0]] = new_Reg[1]
                        regex_patterns[new_Reg[0]] = new_Reg[2]
                        existing = None
    return render_template('add_regex_method.html', existing=existing, regex_groups=regex_groups, 
                           regex_patterns=regex_patterns, regex_logs=regex_logs, logs=logs, alert=alert)

@bp.route("/add/", methods = ['GET', 'POST'])
def add_log_file():
    available = ['access','error','fail2ban']
    alert = None  
    with pool.connection() as conn:
        cur = conn.cursor()  
        existing = cur.execute('SELECT name,location FROM logfiles').fetchall()
        existing = {entry[0]: entry[1] for entry in existing if existing}
        for name in existing.keys():
            if name in available:
                available.remove(name)                
        # Make new log
        if request.method == 'POST' and request.form['log_location']:
            location = Path(request.form['log_location'])
            if location.stem in existing.keys():
                alert = ('Existing log specified. Click {location.stem} to modify its location.', 'warning')
            else:
                ok_log, alert = validate_LogFile(location, False)
                if ok_log:
                    alert = make_LogFile(conn, cur, ok_log)                    
            if alert and alert[1] == 'success':
                existing = cur.execute('SELECT name,location FROM logfiles').fetchall()
                existing = {entry[0]: entry[1] for entry in existing if existing}
                for name in existing.keys():
                    if name in available:
                        available.remove(name)                            
    return render_template('add_log_file.html', available=available, 
                           alert=alert, existing=existing)

@bp.route("/<log_file>/location/", methods = ['GET', 'POST'])
def edit_log_file(log_file):
    alert = None
    with pool.connection() as conn:
        cur = conn.cursor()  
        allowed = [name[0] for name in cur.execute('SELECT name FROM logfiles').fetchall()]
        if log_file not in allowed:
            current_app.logger.info('Invalid URL, redirecting to home')
            return redirect(url_for('home.home'))            
        location = cur.execute('SELECT location FROM logfiles WHERE name=%s', (log_file,)).fetchone()[0]
        _, alert = validate_LogFile(Path(location), None) # check location
            
        # Form submitted
        if request.method == 'POST' and 'confirm_delete' in request.form:
            alert = delete_LogFile(conn,cur,log_file)
            if not alert:
                current_app.logger.info(f'{log_file} deleted! redirecting to home')
                return redirect(url_for('home.home'))      
        elif request.method == 'POST' and 'update' in request.form and request.form['log_location'] != location:
            ok_log, alert = validate_LogFile(Path(request.form['log_location']), log_file)
            if ok_log:
                alert = edit_LogFile(conn, cur, ok_log)
            if alert and alert[1] == 'success':
                location = str(ok_log.location)   
    
    return render_template('edit_log_file.html', log_file=log_file, 
                           location=location, alert=alert)

@bp.route("/<log_file>/parse/", methods = ['GET'])
def parse_log_file(log_file):
    with pool.connection() as conn:
        cur = conn.cursor()           
        allowed = [name[0] for name in cur.execute('SELECT name FROM logfiles').fetchall()]
        if log_file not in allowed:
            current_app.logger.info('Invalid URL, redirecting to home')
            return redirect(url_for('home.home'))     
        try:
            if log_file == 'fail2ban':
                record, alert, data = parsef2b(conn, cur, log_file)
            else:
                record, alert, data = parse(conn, cur, log_file)
        except Exception as e:
            alert = (str(e), 'danger')
            record = None
            data = cur.execute('SELECT lastparsed, modified, regex_1, regex_2, regex_time FROM logfiles WHERE name=%s', (log_file,)).fetchone()
    return render_template('parse_log.html', log_file=log_file, record=record, 
                           alert=alert, data=data, check=datetime(1,1,1))

@bp.route("/<log_file>/regex/", methods = ['GET', 'POST'])
def edit_log_regex(log_file):
    alert = test_results = None
    time_warning = False
    alias = {'regex_1':'Primary', 'regex_2':'Secondary', 'regex_time':'Time Skip'}       
    with pool.connection() as conn:
        cur = conn.cursor()    
        allowed = [name[0] for name in cur.execute('SELECT name FROM logfiles').fetchall()]
        if log_file not in allowed:
            current_app.logger.info('Invalid URL, redirecting to home')
            return redirect(url_for('home.home'))
        allowed.remove(log_file) # list of other logs for links
        
        # log's methods            
        log_methods = {}
        log_methods['regex_1'], log_methods['regex_2'], log_methods['regex_time'] = \
        cur.execute("SELECT regex_1,regex_2,regex_time FROM logfiles WHERE name=%s", (log_file,)).fetchone()

        # available methods for forms, groups included in query         
        regex_methods = cur.execute('SELECT name, groups FROM regex_methods').fetchall()
        regex_methods = {entry[0]: entry[1] for entry in regex_methods if regex_methods}           
        
        # Test Regex selected
        if request.method == 'POST' and 'test_regex' in request.form:
            try:
                test_results = regex_test(cur, log_file, alias)
            except Exception as e:
                alert = (str(e), 'danger')
        # Add/Modify Log Regex    
        elif request.method == 'POST' and 'save_log_regex' in request.form:
            new_regex = {key: request.form[key] for key in request.form if key != 'save_log_regex'}
            new_regex['regex_2'] = None if log_file == 'fail2ban' else new_regex['regex_2']
            for key,item in new_regex.items():
                if item == '':
                    new_regex[key] = None 
            if new_regex != log_methods: # check for new values
                made, alert = regex_LogFile(conn, cur, new_regex, log_file)
                if made: # update info for page                       
                    log_methods['regex_1'], log_methods['regex_2'], log_methods['regex_time'] = \
                    cur.execute("SELECT regex_1,regex_2,regex_time FROM logfiles WHERE name=%s", (log_file,)).fetchone()      
            else:
                alert = ('Specify new methods to save changes', 'warning')            
        # log methods display 
        if list(log_methods.values()) != [None]*3:
            method_info = {(alias[role], name): regex_methods[name] for role,name in log_methods.items() if name!= None}        
            scheme = [column[0] for column in \
            cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s", (log_file,)).fetchall()]
            if log_methods['regex_time'] and len(regex_methods[log_methods['regex_time']]) > 1:
                time_warning = True
        else:
            scheme = None
            method_info = None                
    template = 'edit_log_regex_f2b' if log_file == 'fail2ban' else 'edit_log_regex'
    return render_template(f'{template}.html', method_info=method_info, alias = alias, others=allowed,
                           log_file=log_file, regex_methods=regex_methods, scheme=scheme, alert=alert, 
                           log_methods=log_methods, test_results=test_results, time_warning=time_warning)