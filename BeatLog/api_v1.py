from flask import (
    Blueprint, render_template, request, current_app, abort, url_for, json#, redirect, 
)
from datetime import datetime, timedelta
from psycopg import sql
from .db_pool import pool
from .ops_report import table_build
from .ops_api_v1 import summary, bandwidth
from urllib.request import Request
from urllib.request import urlopen

bp = Blueprint('api_v1', __name__, url_prefix='/api')

@bp.route("/help/", methods = ['GET', 'POST'])
def api_help():
    specs = {val:None for val in ['home','outside','fail2ban', 'geo']}
    if request.method == 'POST' and 'load_example' in request.form:
        spec = request.form['load_example']
        data = json.dumps(json.loads(urlopen(Request(url_for('api_v1.api_v1',_external=True,api_spec=spec))).read().decode('utf-8')),indent=1)
        specs[spec] = data
    return render_template('api_help.html', specs=specs)
                                                  
@bp.route("/v1/summary/<api_spec>", methods = ['GET'])
def api_v1(api_spec):
    api_spec = api_spec.lower()
    print(api_spec)
    if api_spec not in ['all','home','outside','fail2ban', 'geo']:
        abort(422, description = f'''Invalid specification for api/v2/summary/<span class="text-danger">{api_spec}</span>
        <br>Valid Options: <span class="text-success">"home", "outside", "fail2ban", "geo", "all".</span>''')
    end = datetime.now()
    start = end - timedelta(days=1)
    data=dict(time_bounds=dict(start=start.strftime('%x %X'),end=end.strftime('%x %X')))    
    with pool.connection() as conn:
        cur = conn.cursor()
        if api_spec == 'all':
            for val in ['home','outside','fail2ban','geo']:
                data[val] = summary(start,end,val,cur)
        else:
            data[api_spec] = summary(start,end,api_spec,cur)           
    return data
    
@bp.route("/v1/bandwidth/<path:api_spec>", methods = ['GET'])
def api_v1_bandwidth(api_spec):
    api_spec = api_spec.split('=')   
    with pool.connection() as conn:
        cur = conn.cursor()
        data = bandwidth(api_spec,cur)
    if type(data) == str:
        abort(422, data)
    return data

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    