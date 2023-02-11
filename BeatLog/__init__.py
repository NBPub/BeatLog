from flask import Flask, render_template
from pathlib import Path
import logging
from os import getenv
from .db import db_connect, db_startup, conninfo
from .scheduler_tasks import init_tasks
from time import sleep

def create_app(test_config=None):
    app = Flask(__name__) # FLASK_APP configured via environmental variables

    if not app.debug: # Gunicorn logging for deployment
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    else:
        app.logger.setLevel(logging.INFO) # INFO level for debug
    
    # check DB connection, try up to 4 times to wait for postgres
    i = 0
    while i < 4:
        app.logger.info('Attempting database connection . . .')
        check = db_connect(conninfo)
        i+=1
        if check:
            app.logger.critical(f'Database {check}') 
            if check.find('FATAL:') != -1:
                i = 4 # critical failure, exit
                app.logger.critical('Fatal error, getting out')
            elif i<4:                
                app.logger.info(f'trying again, {i+1}/4 attempts . . .')
                sleep(2+i) # db container may be readying, wait and try again          
        else:
            app.logger.info('Database connection established.') # success
            i=5 # success   
    if i == 5:
        check = db_startup(conninfo) # setup tables, settings if they don't exist  
        app.logger.info('Database ready.') if not check else app.logger.critical(check)
    if i < 5 or check: # failure with startup or no connection
        @app.route("/")
        @app.route("/home")
        def noDB():
            return render_template('noDB.html', err=check)
        return app
        
    # scheduler tasks
    check_IP = getenv('check_IP',default='12')
    check_Log = getenv('check_Log',default='3')
    try:
        check_IP = int(check_IP)
        check_Log = int(check_Log)
        if check_IP > 0 or check_Log > 0:
            from .scheduler import scheduler 
            scheduler.init_app(app)
            app.logger.info('Scheduler initialized.')
            init_tasks(check_IP,check_Log, scheduler, conninfo)
            scheduler.start()
            app.logger.info('Scheduled tasks enabled:')
            app.logger.info(f" home IP check every {check_IP} hours, starting in 30s" 
                            if check_IP else " home IP check disabled")
            app.logger.info(f" log check every {check_Log} hours, starting in 15 min" 
                            if check_Log else " log check disabled")
        else:
            app.logger.info('Scheduler disabled.')
    except Exception as e:
        app.logger.info(f'Error with scheduled tasks\n{e}')    

    # Register error handlers
    @app.errorhandler(404)
    def error_page(e):
        return render_template('app_error404.html', e=e), 404    
    @app.errorhandler(500)
    def error_page(e):
        # check status of pool
        from .db_pool import pool
        pool.check()
        sleep(3)
        check = pool.get_stats()               
        if check['pool_available'] == 0:
            message=['Database connection lost, restart container to access web interface. Scheduled tasks should continue (check logs)', 'danger']
        else:
            message = ['Probable database connection error. Apologies for the convenience, retry attempt.', 'info']           
        return render_template('app_error500.html', e=e, message=message), 500     
    
    # register Blueprints
    from . import home, geography, logs, db_view
    app.register_blueprint(home.bp)
    app.register_blueprint(geography.bp)
    app.register_blueprint(logs.bp)
    app.register_blueprint(db_view.bp)
    
    app.logger.info('. . . starting BeatLog . . .')  
    return app