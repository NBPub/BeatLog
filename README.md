# <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> BeatLog

## Overview | [Documentation](/docs#contents)
- [Background](#background)
- [Features](#features)
	- [Database](#database)
	- [Data Report](#report-demo)
	- [Visitor Map](#visitor-map-demo)	
- [Installation](#installation)
	- [Docker](#docker-compose)
	- [Parameters](#parameters)
	- [Data Sources](#data-sources)	
	- [Optional Extras](#extra-options)	
	- [Updates](#updating-postgresql-container), [Container Interaction](#shell-acess-to-beatlog-container)
- [Setup](#application-setup)
- [Development](#development)
	- [Feedback](#development)
	- [In Progress](#submit-bugs-or-feedback)	
	- [Local Installation](#local-installation---python-venv)
	- [Pre-Release Notes](#pre-release-changelog)
	
## Background

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Jinja](https://img.shields.io/badge/jinja-white.svg?style=for-the-badge&logo=jinja&logoColor=black)
![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)
![Chart.js](https://img.shields.io/badge/chart.js-F5788D.svg?style=for-the-badge&logo=chart.js&logoColor=white)
<img src="https://camo.githubusercontent.com/efe5825f7b954f1bdfea52541875c2d3c05da61c645a59d4b08c03e1ff6fbc4c/68747470733a2f2f7261776769742e636f6d2f4c6561666c65742f4c6561666c65742f6d61696e2f7372632f696d616765732f6c6f676f2e737667" 
title="Leaflet.js" style="height:30px;width:auto;">
<img src="https://static.maxmind.com/d2007b9fb8c2a6f15a54/images/maxmind-header-logo-compact-alt.svg" 
title="Leaflet.js" style="height:30px;width:auto;">
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=purple)

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

----

See the [BeatLog Guide](/docs#parsing) for a full list of features. The **Database**, **Report**, and **Visitor Map** are briefly highlighted here.

### Database

Data is saved in a PostgreSQL database and can be used for your own purposes. 
See the [Processed Data](/docs#processed-data) section in the Docs to see the table and field schema used for parsed log data, 
and [Database Explorer](/docs#database-explorer) to see how data can be queried and viewed within **BeatLog**. 
A simple [JSON API](/docs/API.md#simple-json-api) can return summaries for various categories in the past day. 


<details><summary>Database Query - fail2ban Log</summary>

![dataview](/docs/pics/query_3.png "Query result table (entire table not shown).") 

</details>

Adminer [can be installed](#extra-options) to facilitate interaction with the database.

<details><summary>Adminer - Database Overview</summary>

![Adminer](/docs/pics/adminer.png "BeatLog tables, viewed in Adminer")

</details>

----

### Report [|demo|](https://nbpub.github.io/BeatLog/#scrollspyTop)

A report synthesizes all log data from the previous few days or a custom date range. 
Charts are integrated using [CanvasJS](https://canvasjs.com/), and [Bootstrap](https://getbootstrap.com/) is used for tables and styling. 
**[Documentation](/docs#report-demo)**
 - Analyze **home** and **outside** connections against fail2ban **finds, bans,** and **ignores** to assess efficacy of [fail2ban filters](https://fail2ban.readthedocs.io/en/latest/filters.html).
 - Scrutinize traffic from frequent visitors, monitor popular client requests
 - **Known Devices** can be identified and separated from other outside connections
   - ex: connections with a [user-agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) of `DSub`, 
 matching requests from a [Subsonic Android app](http://subsonic.org/pages/apps.jsp#dsub), may be [separated from other Outside connections](/docs#known-devices)

----

### Visitor Map [|demo|](https://nbpub.github.io/BeatLog/#scrollspyVisitorMap)

Visitor locations can be visualized on an interactive map using [LeafletJS](https://leafletjs.com/) and [OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/) tiles. 
**[Documentation](/docs#visitor-map-demo)**
 - Tool tips show location names and total connections or unique visitors (IPs) over the selected time range
 - Location marker sizes are scaled by total connections or unique visitors
 - Tabular data is presented beneath the map

## Installation

BeatLog [docker images](https://hub.docker.com/r/nbpub/beatlog/tags) are created via **[workflows](https://github.com/NBPub/BeatLog/blob/main/.github/workflows/main.yml)** in the following architectures. 
"Stable" images are built and pushed with each release, and "Latest" images are built and pushed with each commit. 
Therefore, the `stable` or `arm32v7-stable` tags are recommended, unless there are pending [updates](#development) that may be desired.

Current release: **[alpha-0.1.4](#https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.4)**, In development: **[alpha-0.1.5](#development)**<br>
| Architecture | Latest Tags | Stable Tags |
| :----: | --- | --- |
| x86-64 | *latest* | *stable*, *alpha-0.1.4* |
| arm64 | *latest*  | *stable*, *alpha-0.1.4* |
| armhf | *arm32v7-latest* | *arm32v7-stable*, *arm32v7-alpha-0.1.4* |

A PostgreSQL database is required, and can be included in the same docker deployment, as shown below.
Or, connect to an existing database, by providing connection settings under `environment:`. 

Logs and other files are added to the container via [volumes](https://docs.docker.com/storage/volumes/). 
See the [data sources](#data-sources) section for specific files in the mounted directories and their usage.
In the example below, the specified directories, and their contents, will be available within a created `/import/` directory.

*It is important to mount files that may change (log turnover, changed fail2ban settings, MaxMindDB updates) indirectly via their parent directories. Directly mounted files will not update within the container.*

The [compose parameters](#parameters) are detailed in the next section. Optional `healthcheck` and `adminer` additions are shown [below](#extra-options).

*With an existing, connectable database,* `depends_on:` *and the following lines are not needed. Ensure a database with the name specified in BeatLog's environment exists.*

### Docker [Compose](https://docs.docker.com/compose/)

```yaml
---
version: "2.1"
services:
  beatlog:
    image: nbpub/beatlog:stable
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
      - /path_to/swag_config/log:/import/log # NGINX and fail2ban logs
      - /path_to/swag_config/fail2ban:/import/fail2ban # fail2ban jail.local
      - /path_to/swag_config/geoip2db:/import/geoip2db # MaxMindDB
    depends_on:
      - db
  db:
    image: postgres:15
    container_name: beatlog_db
    ports:
      - 5432:5432
    environment:
      - POSTGRES_USER=beatlog
      - POSTGRES_PASSWORD=changeme
      - TZ=Pacific/Galapagos	  
    volumes:
      - /path_to/beatlog_conifg/db:/var/lib/postgresql/data # recommended
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
| `/path/to/log_directory:`<br>`/path/in/container` | Add log files, fail2ban jail, and MaxMindDB to container, to be read by **BeatLog**. See [data sources](#data-sources) below |
| `/swag_config/<subdirectory>:`<br>`/import/<subdirectory>` | example for SWAG structure in [setup guide](/docs#data-sources) |
| *. . .* | *. . .* |
| **postgres db ports**  | ---- |
| `5432:5432` | Default database port. If the external port is changed, then `db_port` must be specifed for the beatlog container |
| **postgres db environment**  | ---- |
| `POSTGRES_USER=beatlog` | If changed from `beatlog`, `db_user` and `db_database` must be specified for the beatlog container |
| `POSTGRES_PASSWORD=changeme` | PostgreSQL database password, should match `db_password` |
| `TZ=Pacific/Galapagos` | See above |
| **postgres db volumes**  | ---- |
| `/path_to/beatlog_conifg/db:`<br>`/var/lib/postgresql/data` | *[Recommended](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)*: Store database files in a location of your choosing. Facilitates PostgreSQL updates. |

### Data Sources

**BeatLog** reads the following files for the information described. 
See the [Parsing](/docs#parsing) and [Processed Data](/docs#processed-data) sections of the **[Guide](/docs#contents)** for more information.

- **NGINX reverse proxy**
	- access.log - *client requests to the server*
	- error.log - *client request errors and associated severity levels*
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
  beatlog:
    image: nbpub/beatlog:stable
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
  db:
    image: postgres:15
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "beatlog"]
      interval: 300s
      start_period: 30s
```
</details>

- Add an [Adminer](https://www.adminer.org/) container to interact with your database. Database adjustments outside **BeatLog** are *not* supported and could break functionality. 

<details><summary>Adminer</summary>

*Visit* `<server>:8080` *and login to the postgresql database to view tables and data.*

```yaml
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

### Updating PostgreSQL container

<details><summary>Instructions</summary>

**BeatLog** should work well with PostgreSQL 14 and 15.
As mentioned above, if the database data is mounted to a volume, then upgrading should be as easy as deleting the old image and recreating a new container with the same volume. 
Release logs for PostgreSQL should be checked for any breaking changes.

If the volume was not mounted, upgrading PostgreSQL may erase existing data. In this case, data can be transferred from PostgreSQL containers. 
See **[Migration Between Releases](https://www.postgresql.org/docs/9.0/migration.html)** for more info, and also: 
 * [docker exec](https://docs.docker.com/engine/reference/commandline/exec/)
 * [pg_dumpall](https://www.postgresql.org/docs/current/app-pg-dumpall.html)
 * [docker cp](https://docs.docker.com/engine/reference/commandline/cp/)

The following shows how to manually copy existing database data to a new container. After following these steps, update the container information as needed in the **BeatLog** environment.
```bash
# 1. enter existing container "beatlog_db"
docker exec -it beatlog_db /bin/bash

# 2. pg_dumpall into convenient directory, exit container
cd home
pg_dumpall -U beatlog > db.out
exit

# 3. copy to local directory, then into new database container "beatlog_db_NEW"
docker cp beatlog_db:/home/db.out  /path/of/choosing
docker cp /path/of/choosing/db.out  beatlog_db_NEW:/home

# 4. enter new container and execute script
docker exec -it beatlog_NEW /bin/bash
psql -f db.out -U beatlog postgres
 ```
</details>

### Shell Acess to BeatLog Container

<details><summary>Docker Exec example</summary>

Explore **BeatLog** container using [docker exec](https://docs.docker.com/engine/reference/commandline/exec/), for example, investigate Python environment:


```shell
# 1. enter existing container "beatlog"
docker exec -it beatlog_db /bin/sh

# 2. pip freeze to view installed packages and versions
python -m pip freeze
```

</details>

## Application Setup

Create the container, monitor logs for proper startup, and then navigate to the WebUI at the port specified `http://<your-ip>:5000`.<br>**[Setup Guide](/docs#setup)**

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

### In Progress, alpha-0.1.5

[Details](#pre-alpha-016-details), [Previous Versions](#pre-release-changelog)

- Features
  - Add features to simple JSON API
    - total bandwidth from access log with filters
	- organizing code for API section, more ready to add features. adjusted URL scheme
	- [documentation](/docs/API.md#simple-json-api) in progress
  - allow for SSL in deployment. 
    - Copy to clipboard button won't work in most browsers without connecting **BeatLog** as `localhost` or adding a certificate for LAN connections.
	- Enable via environmental variable, if enabled Gunicorn should look for cerificates / keyfiles. This way a key can be added and "activated" after initial setup.
- Bugfixes
  - Do better to ensure that this release is "stable", now that I'm using "stable" tags.
- No longer building **arm32v7** image with each commit, will only build for stable releases

### Possible Improvements

<details><summary>show/hide</summary>

- Development
  - utilize row factories with psycopg to make cleaner database selections
  - use template file for SQL commands to clean up code
  - add tests for code
  - consider smarter way to gather regex methods across functions
  - solve possible issues with SQL creation: [Home Ignores](/docs#home-ignorable)
- Features
  - visitor maps, pan to location from table entry
  - fail2ban filter testing
</details>

### Local Installation - Python venv

- *Required: Python 3.10, connectable postgresql database*
- Add **[BeatLog folder](https://github.com/NBPub/BeatLog/tree/main/BeatLog)** and **[requirements.txt](https://github.com/NBPub/BeatLog/blob/main/requirements.txt)** into a new directory
- Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
- Install requirements `pip install -r requirements.txt`
  - *Note:* Docker images are built with each commit and without version specification for the packages. This allows gradual updates, but also means the [requirements.txt](/requirements.txt) may not work for your system. The packages listed below can be installed individually.
  - Packages: [Flask](https://flask.palletsprojects.com/), [Flask-APScheduler](https://github.com/viniciuschiele/flask-apscheduler), [python-dotenv](https://github.com/theskumar/python-dotenv), [psycopg3](https://www.psycopg.org/psycopg3/), [geoip2](https://github.com/maxmind/GeoIP2-python)
  - *[gunicorn](https://gunicorn.org/) used in deployment, Flask's Werkzeug can be used for local use*
- Create and populate a **.env** file, model after docker-compose [example](#docker-compose)
  - *Note:* `FLASK_APP=beatlog` is required, `FLASK_RUN_HOST` and `FLASK_RUN_PORT` can be used to change access options. 
  - See links below for details
- Run flask app `flask run` or in debug mode `flask --debug run`

See the Flask [Installation](https://flask.palletsprojects.com/en/2.2.x/installation/) and [Quickstart](https://flask.palletsprojects.com/en/2.2.x/quickstart/) docs for details on these steps.

### Pre-Release Changelog

| Version ([Docker Hub](https://hub.docker.com/r/nbpub/beatlog/tags)) | Notes |
| :----: | --- |
| alpha-0.1.0 | Initial release, testing docker deployment. Flask App environmental variables must be used with this image, similar to Local Installation. Internal port is `5000` for this container. |
| alpha-0.1.1 | Switched WSGI from **Werkzeug** to **Gunicorn**, updated compose example. Minor fixes / tweaks. Working to properly implement Gunicorn, APScheduler, psycopg3 together. |
| alpha-0.1.1t | `NullConnectionPool` version of alpha-0.1.1. may be more stable and less load on postgresql, might be slower. ***psycogp3** [ConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#connection-pools) vs. [NullConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools)* |
| alpha-0.1.2, alpha-0.1.2t | Improved contruction of SQL queries across all functions and pages, with care for [SQL Injection risks](https://www.psycopg.org/psycopg3/docs/basic/params.html#danger-sql-injection). Docker images built via Github [workflow](/actions/workflows/main.yml). Added [demo page](https://nbpub.github.io/BeatLog/). Bugfixes and improvements. |
| alpha-0.1.3, alpha-0.1.3t | **BREAKING: altered database schema! [notes](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2).**<br><br> Added **DB Query** and **View** [pages](/docs#database-explorer) to access database within BeatLog. Improved handling of **Known Devices.** Added location fill to scheduled log parsing. Bugfixes and improvements. Last NullConnectionPool release. |
| alpha-0.1.4 | Removed support for unauthorized log, [link for migration](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3). Added simple [API](/docs/API.md#simple-json-api).<br><br>No more NullConnectionPool tag. All docker images built and pushed via github actions now. |
| alpha-0.1.5 | Additional API features, and API code organization. Bugfixes / aesthetic improvements. Expanding API documentation and help page. |

### pre alpha-0.1.6 details

<details><summary>═════════</summary>

- JSON API
  - new feature: **[bandwidth](/docs/API.md#bandwidth)** - returns total bandwidth from access log.
    - filter return by specifying FIELD and VALUE. String matching provided for `tech`,`URL`, and `referrer`
	- optional filter by date with start/stop inputs. only supporting UNIX format for now
	- see documentation (linked above) for more details, ***in progress***
  - named only previous feature **[summary](/docs/API.md#data-summary)**. each "feature" on separate URLs.
  - separated code into two files. Additional features can be added to existing blueprint.
    - *future development:* can copy blueprint and establish `API v2` to maintain existing features through unstable releases
- Docker Image Workflows
  - no longer building "latest" image automatically with each commit for `armhf` AKA `arm32v7` architectures, can build on request
  - will continue building "stable" images with each release
- Bugfixes to make a more "stable" release. Various aesthetic / navigation improvements 
  - API bugfixes
  - Updated [Bootstrap](https://getbootstrap.com/docs/) from to 5.3 from 5.2
  - .

</details>

### pre alpha-0.1.5 details

<details><summary>═════════</summary>

- Version Control, Image management
  - renamed existing workflow to build+push docker images with each commit. Tags still same name, `latest`.
  - created additional workflow to build+push docker images with each release. Tags will be version `alpha-0.1.4` and `stable`.  
  - No more docker images built+pushed by me, all from within Github.
- Code Cleaning
  - removed unauthorized.log support. removed comment blocks for NullConnectionPool versions (see [changes](/docs/NullConnectionPool.md#background)).
- API v1
  - JSON API to retrieve basic stats, [help page](/docs/API.md#simple-json-api)
- Bug Fixes / Minor Improvements
  - fixed issues with changed code for fail2ban jail page, Known Device settings
  - added check for existing data before API calls
  - various aesthetic / navigation improvements


</details>



### pre alpha-0.1.4 details

<details><summary>═════════</summary>

- Database Schema
  - changed datatypes for Settings > **KnownDevices** and Jail > **IgnoreIPs**
  - Added time interval columns, **Findtime** and **Bantime** to Jail.
  - detailed in [alpha-0.1.2 tag](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2).**), manual migrations required prior to update
- DB Features
  - page to query database (access, error, fail2ban logs) and page to view time-ordered results as table
  - various filter options and pre-assembled queries
- Documentation
  - added sections detailing new DB features
  - fixes for some images and file paths
- SQL query creation improved **[Known Devices](/docs#known-devices)**
  - devices now input as group of strings, which is stored as text array in database
  - [psycopg3 sql module](https://www.psycopg.org/psycopg3/docs/api/sql.html) then used to craft specific SQL, `WHERE tech = ANY(<list>)` or `WHERE tech != ALL(<list>)`
- Expanded fail2ban jail.local page
  - can now read more than one *ignore* IP address, if present
  - reads and present find and ban times
- Bug Fixes / Minor Improvements
  - various aesthetic / navigation improvements

</details>


### pre alpha-0.1.3 details

<details><summary>═════════</summary>

- Installation, Docker Compose
  - mount directories instead of files to update logs within **BeatLog** container
  - PostgreSQL upgrade instructions
- Docker Image
  - Building **latest** and **arm32v7-latest** tags via Github [workflow](/actions/workflows/main.yml)
  - NullConnectionPool versions uploaded manually for now, may stop later
- Documentation
  - [demonstration page](https://nbpub.github.io/BeatLog/) for Map and Report, added links to docs
- General
  - SQL query creation improved, as per [psycopg3 docs](https://www.psycopg.org/psycopg3/docs/basic/params.html)
    - *need to continue work on *`Known Devices`* and *`Home Ignorable`* [usage](/docs#known-devices)*
  - increased gunicorn worker timeout to 60s, from 30s, to allow for long operations
	- Can revert by 
	  - Timechecks in `Parse All`, individual parsing operations
	  - Analyze report generation with profiler for potential improvements
	  - geography [location lookup](/docs#location-lookup) capped to 20 per attempt
  - Bug Fixes / Minor Improvements
    - various errors fixed
    - added data to report tables
    - various aesthetic / navigation improvements

</details>

Last NullConnectionPool releases! [Notes](/docs/NullConnectionPool.md)

### pre alpha-0.1.2 details

<details><summary>═════════</summary>

- Issue with psycopg3 connection pool not restoring discarded connections. Related to Gunicorn or app design?
  - general issue of `ConnectionPool` with Gunicorn's forked workers. error may be solved: pool opened and checked after fork, before first request.
  - Scheduled tasks created with `gunicorn --preload`, to run with a single Gunicorn worker.
  - need to figure out how to best use (Flask)-**APScheduler**, **Gunicorn**, and **psycopg3 ConnectionPool** together. 
    - reading up on [server hooks](https://docs.gunicorn.org/en/stable/settings.html#server-hooks)
- If modified location city/country is set to `None`, should save as `NULL` in database.
  - adding note to docs about inability to set "None" as a city or country name, due to above. [Sorry!](https://geotargit.com/called.php?qcity=None)
- Scheduled `parse_all` may cause duplicate prepared statements error
  - monitor, think this is fixed. probably result of spamming home page
- Potential Gunicorn worker timeout for parsing or location fill operations
  - limited geofill to maximum of 20 locations at a time (20-25 second operation), could increase `gunicorn --timeout` from default 30 seconds.
  - what is upper limit for parsing time?
- change fail2ban lastparsed from last saved line to last read line
  - should be less confusing when checking last parsed
- expand documentation*
  - continuous drafting, documenting changes in detail until beta release
- add production WSGI server **[Gunicorn](https://gunicorn.org/)**, using 3 workers for now
  - do workers+ConnectionPool take too many database connections?
  - reading up on Gunicorn server hooks to understand best way to integrate scheduled tasks
  
</details>
