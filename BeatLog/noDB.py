from flask import (
    Blueprint, render_template
)
from os import getenv
from .db import db_connect

bp = Blueprint('noDB', __name__, url_prefix='/')
@bp.route("/", methods = ['GET'])
@bp.route("/home/", methods = ['GET'])
def home():
    check = db_connect(getenv('db_host', 'localhost'),
                       getenv('db_user', 'beatlog'),
                       getenv('db_password'),
                       getenv('db_database', 'beatlog'),
                       getenv('db_port', '5432')) 
    if not check: # should never happen
        check = 'Database connection established, restart container or flask app'
    return render_template('noDB.html', err=check)