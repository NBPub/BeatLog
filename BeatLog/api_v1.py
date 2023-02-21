from flask import (
    Blueprint, render_template, request, current_app, abort, url_for, json#, redirect, 
)
from datetime import datetime, timedelta, date
from psycopg import sql
from .db_pool import pool
from .ops_report import table_build
from .ops_api_v1 import summary, bandwidth
from .ops_log import home_ip
from urllib.request import Request
from urllib.request import urlopen

bp = Blueprint('api_v1', __name__, url_prefix='/api')

@bp.route("/help/", methods = ['GET', 'POST'])
def api_help():
    specs = {val:None for val in ['home','outside','fail2ban', 'geo']}
    ex_bandwidth = round(datetime.now().timestamp())
    ex_bandwidth = f'date={ex_bandwidth-86400}-{ex_bandwidth},referrer=%http://%'
    ex_return = None
    
    if request.method == 'POST' and 'load_example' in request.form: # API data return preview
        spec = request.form['load_example']
        if spec != 'bandwidth':
            data = json.dumps(json.loads(urlopen(Request(url_for('api_v1.api_v1_summary',_external=True,api_spec=spec)))\
                              .read().decode('utf-8')),indent=1)
            specs[spec] = data
        else:
            ex_return = json.dumps(json.loads(urlopen(Request(url_for('api_v1.api_v1_bandwidth',_external=True,
                        api_spec=ex_bandwidth))).read().decode('utf-8')),indent=1)
    
    return render_template('api_help.html', specs=specs, ex_bandwidth=ex_bandwidth, ex_return=ex_return)
                                                  
@bp.route("/v1/summary/<api_spec>", methods = ['GET'])
def api_v1_summary(api_spec): # validate option, establish time bounds, return data
    api_spec = api_spec.lower()
    if api_spec not in ['all','home','outside','fail2ban', 'geo']:
        abort(422, description = f'''Invalid specification for api/v2/summary/<span class="text-danger">{api_spec}</span>
        <br>Valid Options: <span class="text-success">"home", "outside", "fail2ban", "geo", "all".</span>''')
    end = datetime.now()
    start = end - timedelta(days=1)
    data=dict(time_bounds=dict(start=start.strftime('%x %X'),end=end.strftime('%x %X')))    
    with pool.connection() as conn:
        cur = conn.cursor()
        with conn.transaction():
            _ = home_ip(cur)
        if api_spec == 'all':
            for val in ['home','outside','fail2ban','geo']:
                data[val] = summary(start,end,val,cur)
        else:
            data[api_spec] = summary(start,end,api_spec,cur)           
    return data
    
@bp.route("/v1/bandwidth/<path:api_spec>", methods = ['GET'])
def api_v1_bandwidth(api_spec): # FIELD=VALUE or DATE=UNIX-UNIX,FIELD=VALUE        
    # if date specified, extract values and assemble query parameters
    if api_spec.split('=')[0].lower() != 'date':
        # Manually split query at first '=' to allow for '=' use in VALUE 
        split_ind = api_spec.find('=')
        api_spec = [api_spec[0:split_ind],api_spec[split_ind+1:]]
        date_spec = None
    else:
        date_spec = api_spec[0:26]
        try:
            date_spec = date_spec.split('=')[1].split('-')
            date_spec = [datetime.fromtimestamp(int(val)) for val in date_spec] # change to date.fromtimestamp() to round to nearest day
            api_spec = api_spec[27:]               
            split_ind = api_spec.find('=')
            api_spec = [api_spec[0:split_ind],api_spec[split_ind+1:]]
        except Exception as e:
            ex_date = round(datetime.now().timestamp())
            ex_date = (ex_date-86400, ex_date)
            abort(422, f'Invalid timestamp specification for api/v2/bandwidth/<span class="text-success">date={ex_date[0]}-{ex_date[1]},</span> . . .\
                       <br><span class="text-danger">{e}</span>')
    
    # no "=" to split FIELD=VALUE, return NO VALUE error
    if split_ind == -1:
        abort(422, f'Invalid specification for api/v2/bandwidth/. . . <span class="text-success mx-3">FIELD=VALUE</span>\
                   <br>No VALUE! <span class="text-danger mx-3">{api_spec[1]}</span>') # &nbsp;                    
    # Perform SQL, return data + query information
    api_spec[0] = api_spec[0].lower()
    with pool.connection() as conn:
        cur = conn.cursor()
        data = bandwidth(api_spec,date_spec,cur)
    # Invalid API query, error running SQL
    if type(data) == str:
        abort(422, data)
    return data