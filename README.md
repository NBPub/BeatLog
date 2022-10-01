# <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> BeatLog 


## Overview
- [Background](#background)
- [Features](#features)
- [Installation](#installation)
	- [Docker](#docker-compose)
	- [Parameters](#parameters)
	- [Data Sources](#data-sources)	
	- [Optional Extras](#extra-options)	
- [Setup](#application-setup)
- [Development](#development)
	- [Feedback](#development)
	- [Upcoming](#planned-improvements)	
	- [Local Installation](#local-installation---python-venv)
	- [Pre-Release Notes](#pre-release-changelog)
	
## Background

**BeatLog** parses [NGINX](https://www.nginx.com/) reverse proxy and [fail2ban](https://www.fail2ban.org/wiki/index.php/Main_Page) logs into readable tables and reports. 
Use **BeatLog** to assess server traffic and tailor fail2ban filters.

## Features

BeatLog is a [Python](https://www.python.org/) based [web application](https://flask.palletsprojects.com/), and utilizes a [PostgreSQL](https://www.postgresql.org/) database for storage.
Log files are parsed line-by-line using [regex](https://en.wikipedia.org/wiki/Regular_expression). BeatLog provides default patterns for parsing, but each log's regex scheme can be customized.

In addition to parsing data from log files, it categorizes each IP address as coming from "Home" (same IP as server) or "Outside" (anywhere else). 
Location information (coordinates, city, country) can be added to all "Outside" entries, using MaxMind's [GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=en) database 
([SWAG](https://github.com/linuxserver/docker-swag) users, see: [mod installation](https://github.com/linuxserver/docker-mods/tree/swag-maxmind)). 
If only coordinates are provided from the MaxMind database, locations can be ascertained using the [Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/) reverse geocoding API, 
based on [OpenStreetMap](https://www.openstreetmap.org/about) data.

See the [BeatLog Guide](/docs) for a full list of features. The **Report** and **Visitor Map** are briefly highlighted here.

### Report

A report synthesizes all log data from the previous few days or a custom date range. 
Charts are integrated using [CanvasJS](https://canvasjs.com/), and [Bootstrap](https://getbootstrap.com/) is used for tables and styling. 

***[Details and screenshots](/docs#report)***
 - Analyze **home** and **outside** connections against fail2ban **finds, bans,** and **ignores** to assess efficacy of [fail2ban filters](https://fail2ban.readthedocs.io/en/latest/filters.html).
 - Scrutinize traffic from frequent visitors, monitor popular client requests
 - **Known Devices** can be identified and separated from other outside connections
   - ex: connections with a [user-agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) of `DSub`, 
 matching requests from a [Subsonic Android app](http://subsonic.org/pages/apps.jsp#dsub), may be [separated from other Outside connections](/docs#known-devices)


### Visitor Map

Visitor locations can be visualized on an interactive map using [LeafletJS](https://leafletjs.com/) and OpenStreetMap [tiles](https://operations.osmfoundation.org/policies/tiles/). 

***[Details and screenshots](/docs#visitor-map)***
 - Location markers are scaled by total connections or unique visitors (IPs) over the time range

## Installation

BeatLog is available as [docker images](https://hub.docker.com/r/nbpub/beatlog/tags) in the following architectures. 

*current version:* **[alpha-0.1.1](#pre-release-changelog)**
| Architecture | Tag | *NullConnectionPool* |
| :----: | --- | --- |
| x86-64 | *latest* | *alpha-0.1.1t* |
| arm64 | *latest*  | *alpha-0.1.1t* |
| armhf | *arm32v7-latest* | *arm32v7-alpha-0.1.1t* |

A PostgreSQL database is required, and can be included in the same docker deployment, as shown below.
Or, connect to an existing database, by providing connection settings under `environment:`. 

Logs and other files are added to the container via [volumes](https://docs.docker.com/storage/volumes/).
See the [data sources](#data-sources) section for more details on the files added as volumes.
In the example below, they will be available in the `/import` directory.

The [compose parameters](#parameters) are detailed in the next section. Optional `healthcheck` and `adminer` additions are shown [below](#extra-options).

*With an existing database container,* `depends_on:` *and the following lines are not needed. Ensure a database with the name specified in BeatLog's environment exists.*

### Docker [Compose](https://docs.docker.com/compose/)

```yaml
---
version: "2.1"
services:
  beatlog:
    image: nbpub/beatlog:latest
    container_name: beatlog
    user: 1000:1000 # optional	
    ports:
      - 5000:8000 # access from 5000 instead of 8000, for demonstration
    environment:
      - TZ=Pacific/Galapagos
      - db_host=<IP>
      - db_password=changeme	  
      - FLASK_SECRET_KEY=<secretkey>
      - check_IP=12
      - check_Log=3	  
    volumes:
      - /path_to/access.log:/import/access.log
      - /path_to/error.log:/import/error.log
      - /path_to/unauthorized.log:/import/unauthorized.log
      - /path_to/fail2ban.log:/import/fail2ban.log
      - /path_to/jail.local:/import/jail.local # fail2ban jail.local
      - /path_to/GeoLite2-City.mmdb:/import/GeoLite2-City.mmdb # MaxMindDB
    depends_on:
      - db
  db:
    image: postgres
    container_name: beatlog_db
    ports:
      - 5432:5432
    environment:
      - POSTGRES_USER=beatlog
      - POSTGRES_PASSWORD=changeme
      - TZ=Pacific/Galapagos	  
    volumes:
      - /path_to/beatlog_conifg/db:/var/lib/postgresql/data # optional
    restart: unless-stopped   	
```

### Parameters 

Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate `<external>:<internal>` respectively. 
For example, setting ports to `5433:5432` would expose port `5432` from inside the container to be accessible from the host's IP on port `5433` outside the container.

Sensitive data can be passed to compose using [secrets](https://docs.docker.com/engine/swarm/secrets/#use-secrets-in-compose), if desired.

| Parameter | Function |
| :----: | --- |
| **user** | ---- |
| `1000:1000` | Optional [setting](https://docs.docker.com/compose/compose-file/#user) to change the **user** used for the docker container. [See also](https://docs.linuxserver.io/general/understanding-puid-and-pgid) |
| **ports** | ---- |
| `5000:8000` | Example of changing external access port. Internal port, `8000`, should not be changed. |
| **environment**  | ----  |
| `TZ=Pacific/Galapagos` | Timezone should match log files. Defaults to `UTC`. [time zone list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `db_host=<IP>` | IP address or host name of PostgreSQL database, defaults to `localhost` which should fail |
| `db_password=changeme` | PostgreSQL database password, should match `POSTGRES_PASSWORD` |
| `db_port=` | Only needed if **database port** is changed, defaults to `5432` |
| `db_user=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `db_database=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `FLASK_SECRET_KEY=<secretkey>` | Generate a [secret key](https://flask.palletsprojects.com/en/2.2.x/tutorial/deploy/#configure-the-secret-key) for deployment. Default, `dev`, is not suitable |
| `check_IP=12` | Interval (hours) for checking / updating the home IP address, `12` hr default. Specify as integer, or `0` to disable |
| `check_Log=3` | Interval (hours) for checking / parsing the Log Files, `3` hr default. Specify as integer, or `0` to disable  |
| **volumes**  | ---- |
| `/path/to/file:/path/in/container` | Add log files, fail2ban jail, and MaxMindDB to container, to be read by **BeatLog**. See [data sources](#data-sources) below |
| `/file2/:/import/file2` | example for SWAG structure in [setup guide](/docs#data-sources) |
| *. . .* | *. . .* |
| | |
| **postgres db ports**  | ---- |
| `5432:5432` | Default database port. If the external port is changed, then `db_port` must be specifed for the beatlog container |
| **postgres db environment**  | ---- |
| `POSTGRES_USER=beatlog` | If changed from `beatlog`, `db_user` and `db_database` must be specified for the beatlog container |
| `POSTGRES_PASSWORD=changeme` | PostgreSQL database password, should match `db_password` |
| `TZ=Pacific/Galapagos` | See above |
| **postgres db volumes**  | ---- |
| `/path_to/beatlog_conifg/db:/var/lib/postgresql/data` | *[Optional](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)*: Store database files in a location of your choosing. |

### Data Sources

**BeatLog** reads the following files for the information described. 
See the [Parsing](/docs#parsing) and [Processed Data](/docs#processed-data) sections of the **[Guide](/docs#contents)** for more information.

- **NGINX reverse proxy**
	- access.log - *client requests to the server*
	- error.log - *client request errors and associated severity levels*
	- unauthorized.log - *redundant to **access.log**, captures requests with [401 HTTP status codes](https://www.httpstatuses.org/401)*
- **fail2ban**
	- fail2ban.log - *all activity of fail2ban service, relevant information is parsed and the rest ignored*
	- jail.local - *fail2ban settings and activated filters, checks ignored IPs*
- **MaxMindDB**
	- GeoLite2-City.mmdb - *database to match IP addressess to locations, updated twice monthly*

### Extra Options

- Add [healthcheck(s)](https://docs.docker.com/engine/reference/builder/#healthcheck) to indicate container status.

<details><summary>Healthcheck - BeatLog</summary>

*The port number,* `8000` *should match the container's internal port.*

```yaml
version: "2.1"
services:
  beatlog:
    image: nbpub/beatlog:latest
    container_name: beatlog
    .
    .
    .
    healthcheck:
      test: curl -I --fail http://localhost:8000 || exit 1
      interval: 300s
      timeout: 10s
      start_period: 20s
    .
    .
    .
```
</details>

<details><summary>Healthcheck - Postgres</summary>

*The user,* `beatlog` *should match the* `POSTGRES_USER` *specified.*

```yaml
    .
    .
    .
  db:
    image: postgres
    .
    .
    .
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "beatlog"]
      interval: 300s
      start_period: 30s
    .
    .
    .
```
</details>

- Add an [Adminer](https://www.adminer.org/) container to interact with your database. Database adjustments outside **BeatLog** are not supported and could break functionality. 

<details><summary>Adminer</summary>

*Visit* `<server>:8080` *and login to the postgresql database to view tables and data.*

```yaml
    .
    .
    .
  adminer:
    image: adminer
    container_name: beatlog_mgmt	
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - 8080:8080
  db:
    .
    .
    .

```
</details>

## Application Setup

Create the container, monitor logs for proper startup, and then navigate to the WebUI at `http://<your-ip>:5000`.<br>**[Setup Guide](/docs#setup)**

*If a database connection error is presented, check the parameters provided in your compose file and consult the container logs for more information.*

Get the most information from BeatLog following these steps:

1. Specify **[Log File](/docs#log-files)** locations `*/Logs/add/`
2. [Load default **regex methods**](/docs#regex-methods) or create and test your own `*/Logs/add_regex/`
3. [Associate **regex methods**](/docs#adding-regex-to-logs) with **Log Files** to prepare for parsing `*/Logs/<log_file>/regex/`
4. Specify fail2ban **[jail.local](/docs#fail2ban-jail)** location `*/jail/`
5. Specify MaxMind **[GeoLite2-City](/docs#maxminddb)** database location, in **geography settings** `*/settings#geography`
6. Add a user-agent for the **[Nominatim API](/docs#maxminddb)** to fill unnamed locations, in **geography settings**
7. [Parse](/docs#parsing) Logs!

## Development

### [Submit](https://github.com/NBPub/BeatLog/issues/new) bugs or feedback.

- ~~*Issue with psycopg3 connection pool not restoring discarded connections. Related to Gunicorn or app design?~~
  - general issue of `ConnectionPool` with Gunicorn's forked workers. error may be solved: pool opened and checked after fork, before first request.
  - Scheduled tasks created with `gunicorn --preload`, to run with a single Gunicorn worker.
  - need to figure out how to best use (Flask)-**APScheduler**, **Gunicorn**, and **psycopg3 ConnectionPool** together. 
    - reading up on [server hooks](https://docs.gunicorn.org/en/stable/settings.html#server-hooks)
- ~~*If modified location city/country is set to* `None`, *should save as* `NULL` *in database*.~~
  - adding note to docs about inability to set "None" as a city or country name, due to above. [Sorry!](https://geotargit.com/called.php?qcity=None)
- ~~*Scheduled* `parse_all` *may cause duplicate prepared statements error*~~
  - monitor, think this is fixed. probably result of spamming home page
- ~~*Potential Gunicorn worker timeout for parsing or location fill operations*~~
  - limited geofill to maximum of 20 locations at a time (20-25 second operation), could increase `gunicorn --timeout` from default 30 seconds.
  - what is upper limit for parsing time?
- ~~*change fail2ban lastparsed from last saved line to last read line*~~
  - should be less confusing when checking last parsed

### Planned Improvements

**In Progress**
- ~~expand documentation~~
  - *drafting*
- ~~add production WSGI server~~ **[Gunicorn](https://gunicorn.org/)**, using 3 workers for now
  - *do workers+ConnectionPool take too many database connections?*
  - *reading up on Gunicorn server hooks to understand best way to integrate scheduled tasks*

**Future**
- Development
  - Github workflow for publishing Docker images
  - utilize row factories with psycopg to make cleaner database selections
  - use template file for SQL commands to clean up code
  - add tests for code
  - asyncio for scheduled tasks and/or other routines
  - consider smarter way to gather regex methods across functions
- Features
  - pan to location on maps (using table links)
  - fail2ban filter testing
  - failed regex analysis
  - data viewer page: forms for easy SQL selects --> present data in tables

### Local Installation - Python venv

- *Required: connectable postgresql database*
- Add **[BeatLog folder](https://github.com/NBPub/BeatLog/tree/main/BeatLog)** and **[requirements.txt](https://github.com/NBPub/BeatLog/blob/main/requirements.txt)** into a new directory
- Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
- Install requirements `pip install -r requirements.txt`
- Create and populate a **.env** file, model after docker-compose [example](#docker-compose)
  - *Note:* `FLASK_APP=beatlog` is required, `FLASK_RUN_HOST` and `FLASK_RUN_PORT` can be used to change access options. 
  - See links below for details
- Run flask app `flask run` or in debug mode `flask --debug run`

See the Flask [Installation](https://flask.palletsprojects.com/en/2.2.x/installation/) and [Quickstart](https://flask.palletsprojects.com/en/2.2.x/quickstart/) docs for details on these steps.

### Pre-Release Changelog

| Version (Docker Hub) | Notes |
| :----: | --- |
| alpha-0.1.0 | Initial release, testing docker deployment. Flask App environmental variables must be used with this image, similar to Local Installation. Interal port is `5000` for this container. |
| alpha-0.1.1 | Switched WSGI from **Werkzeug** to **Gunicorn**, updated compose example. Minor fixes / tweaks. Working to properly implement Gunicorn, APScheduler, psycopg3 together. |
| alpha-0.1.1t | `NullConnectionPool` version of alpha-0.1.1. may be more stable and less load on postgresql, might be slower. |

***psycogp3** [ConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#connection-pools) vs. [NullConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools)*