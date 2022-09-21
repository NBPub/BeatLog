from flask import Flask, render_template
from pathlib import Path
import logging
from os import getenv
from .db import db_connect
from .scheduler_tasks import init_tasks

def create_app(test_config=None):
    app = Flask(__name__) # FLASK_APP configured via environmental variables
    
    if not app.debug: # Gunicorn logging for deployment
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    else:
        app.logger.setLevel(logging.INFO) # INFO level for debug

    # register DB, provide error page on failed connection
    with app.app_context():
        check = db_connect(getenv('db_host', 'localhost'),
                           getenv('db_user', 'beatlog'),
                           getenv('db_password'),
                           getenv('db_database', 'beatlog'),
                           getenv('db_port', '5432')) 
        if check:
            app.logger.critical('Database connection failed: %s', check)
            from . import noDB
            app.register_blueprint(noDB.bp)
            return app           
    app.logger.info('Database ready, connection established.')
    
    # Register error handlers
    @app.errorhandler(404)
    def error_page(e):
        return render_template('app_error404.html', e=e)
    @app.errorhandler(500)
    def error_page(e):
        return render_template('app_error500.html', e=e)
        
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
            init_tasks(check_IP,check_Log, scheduler)
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
    
    # register Blueprints
    from . import home, geography, logs
    app.register_blueprint(home.bp)
    app.register_blueprint(geography.bp)
    app.register_blueprint(logs.bp)    
      
    return app # https://flask.palletsprojects.com/en/2.2.x/tutorial/factory/