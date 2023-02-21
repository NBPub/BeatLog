# BeatLog Local Installation

**BeatLog** can be installed and run locally, most easily within a Python [virtual environment](https://docs.python.org/3/library/venv.html). 
This is how I develop **BeatLog**. I specify my existing database connection parameters in an `.env` file, instead of as environmental variables.


## Python venv

*Required: Python 3.10, connectable postgresql database*

- Add **[BeatLog folder](https://github.com/NBPub/BeatLog/tree/main/BeatLog)** and **[requirements.txt](https://github.com/NBPub/BeatLog/blob/main/requirements.txt)** into a new directory
- Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
- Install requirements `pip install -r requirements.txt`
  - *Note:* Docker images are built with each commit and without version specification for the packages. This allows gradual updates, but also means the [requirements.txt](/requirements.txt) may not work for your system. The packages listed below can be installed individually.
    - Packages: [Flask](https://flask.palletsprojects.com/), [Flask-APScheduler](https://github.com/viniciuschiele/flask-apscheduler), [python-dotenv](https://github.com/theskumar/python-dotenv), [psycopg3](https://www.psycopg.org/psycopg3/), [geoip2](https://github.com/maxmind/GeoIP2-python)
    - *[gunicorn](https://gunicorn.org/) used in deployment, Flask's Werkzeug can be used for local use*
- Create and populate a **[.env](https://github.com/theskumar/python-dotenv)** file, model after docker-compose [parameters](/README.md#docker-compose). 
  - See [below](#sample-dot-env) for example.
  - *Note:* `FLASK_APP=beatlog` is required, `FLASK_RUN_HOST` and `FLASK_RUN_PORT` can be used to change access options. 
- Run Flask app `flask run` or in debug mode `flask --debug run`
  - See links below for details on running a Flask application

See the Flask [Installation](https://flask.palletsprojects.com/en/2.2.x/installation/) and [Quickstart](https://flask.palletsprojects.com/en/2.2.x/quickstart/) docs for details on these steps, 
including OS-specific [guidance](https://flask.palletsprojects.com/en/2.2.x/installation/#virtual-environments) on setting up a Python virtual environment.

## Sample Dot Env

```Dotenv
# Specify commented variables if changed from values shown (defaults)
# Speciy user-specific <values>

FLASK_APP=beatlog
# FLASK_RUN_HOST=0.0.0.0
# FLASK_RUN_PORT=5000
FLASK_SECRET_KEY=dev

db_host=<IP/hostname>
# db_user=beatlog
db_password=<password>
# db_port=5432

# Scheduled Tasks
check_IP=0 # disabled
check_Log=0 # change to enable

# Timezone
TZ=<timezone>
```