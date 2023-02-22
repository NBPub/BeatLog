# <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> BeatLog

## Overview | [Documentation](/docs#beatlog-documentation-)
- [Background](#background)
- [Features](#features)
	- [Database](#database)
	- [Data Report](#report-demo)
	- [Visitor Map](#visitor-map-demo)	
- [Installation](#installation)
	- [Docker](#docker-compose)
	- [Parameters](#parameters)
	- [Data Sources](#data-sources)	
	- *[Installation Extras](/docs/Installation/Installation_Extras.md#beatlog-installation-options) +*
- [Setup](#application-setup)
	- *[Setup Guide](/docs#setup-guide-contents) +*
- [Development](#development)
	- [Feedback](#development)
	- [In Progress](#submit-bugs-or-feedback)	
	- [Pre-Release Notes](#pre-release-changelog)
		- *[Detailed Changelog](/docs/Installation/Changelog.md#beatlog-changelog) +*
	- *[Local Installation](/docs/Installation/Local_Installation.md#beatlog-local-installation) +*
	
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

See the [BeatLog Documentation](/docs#beatlog-documentation-) for a full description of features. The **Database**, **Report**, and **Visitor Map** are briefly highlighted here.

### Database

Data is saved in a PostgreSQL database and can be used for your own purposes. 
See the [Processed Data](/docs#processed-data) section in the Docs to see the table and field schema used for parsed log data, 
and [Database Explorer](/docs/Features/Database.md#database-explorer) to see how data can be queried and viewed within **BeatLog**. 
A simple [JSON API](/docs/Features/API.md#simple-json-api) can provides daily summaries and bandwidth statistics. 


<details><summary>Database Query - fail2ban Log</summary>

![dataview](/docs/pics/query_3.png "Query result table (entire table not shown).") 

</details>

Adminer [can be installed](/docs/Installation/Installation_Extras.md#adminer) to facilitate interaction with the database.

----

### Report [|demo|](https://nbpub.github.io/BeatLog/#scrollspyTop)

A report synthesizes all log data from the previous few days or a custom date range. 
Charts are integrated using [CanvasJS](https://canvasjs.com/), and [Bootstrap](https://getbootstrap.com/) is used for tables and styling. 

 - Analyze **home** and **outside** connections against fail2ban **finds, bans,** and **ignores** to assess efficacy of [fail2ban filters](https://fail2ban.readthedocs.io/en/latest/filters.html).
 - Scrutinize traffic from frequent visitors, monitor popular client requests
 - **Known Devices** can be identified and separated from other outside connections
   - ex: connections with a [user-agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) of `DSub`, 
 matching requests from a [Subsonic Android app](http://subsonic.org/pages/apps.jsp#dsub), may be [separated from other Outside connections](/docs/Features/Report.md#known-devices)

**[Documentation](/docs/Features/Report.md#contents)**

----

### Visitor Map [|demo|](https://nbpub.github.io/BeatLog/#scrollspyVisitorMap)

Visitor locations can be visualized on an interactive map using [LeafletJS](https://leafletjs.com/) and [OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/) tiles. 

 - Tool tips show location names and total connections or unique visitors (IPs) over the selected time range
 - Location marker sizes are scaled by total connections or unique visitors
 - Tabular data is presented beneath the map

**[Documentation](/docs/Features/Geography.md#visitor-map-demo)**

----

## Installation

BeatLog [docker images](https://hub.docker.com/r/nbpub/beatlog/tags) are created via **[workflows](https://github.com/NBPub/BeatLog/blob/main/.github/workflows/main.yml)** with the following tags. 
"Stable" images are built and pushed with each release, and "Latest" images are built and pushed with each commit. 
Therefore, the `stable` or `arm32v7-stable` tags are recommended, unless there are pending [updates](#development) that may be desired.

Current release: **[alpha-0.1.5](#https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.5)**, In development: **[alpha-0.1.6](#development)**<br>
| Architecture | Latest Tags | Stable Tags |
| :----: | --- | --- |
| x86-64 | *latest* | *stable*, *alpha-0.1.5* |
| arm64 | *latest*  | *stable*, *alpha-0.1.5* |
| armhf | (*built on request*) | *arm32v7-stable*, *arm32v7-alpha-0.1.5* |

A PostgreSQL database is required, and can be included in the same docker deployment, as shown below.
Or, connect to an existing database, by providing connection settings under `environment:`. 

Logs and other files are added to the container via [volumes](https://docs.docker.com/storage/volumes/). 
See the [data sources](#data-sources) section for specific files in the mounted directories and their usage.
In the example below, the specified directories, and their contents, will be available within a created `/import/` directory.

*It is important to mount files that may change (log turnover, changed fail2ban settings, MaxMindDB updates) indirectly via their parent directories. Directly mounted files will not update within the container.*

The [compose parameters](#parameters) are detailed in the next section. Optional `healthcheck` and `adminer` additions are shown on the [Installation Extras page](/docs/Installation/Installation_Extras.md#beatlog-installation-options).

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

<details><summary><b>Docker Compose Parameters</b></summary>

| Parameter | Function |
| :----: | --- |
| **user** | <br> |
| `1000:1000` | Optional [setting](https://docs.docker.com/compose/compose-file/#user) to change the **user** used for the docker container. [See also](https://docs.linuxserver.io/general/understanding-puid-and-pgid) |
| **ports** | <br> |
| `5000:8000` | Example of changing external access port. Internal port, `8000`, should not be changed. |
| **environment**  | <br>  |
| `TZ=Pacific/Galapagos` | Timezone should match log files. Defaults to `UTC`. [time zone list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `db_host=<IP>` | IP address or host name of PostgreSQL database, defaults to `localhost` which should fail |
| `db_password=changeme` | PostgreSQL database password, should match `POSTGRES_PASSWORD` |
| `db_port=` | Only needed if **database port** is changed, defaults to `5432` |
| `db_user=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `db_database=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `FLASK_SECRET_KEY=<secretkey>` | Generate a [secret key](https://flask.palletsprojects.com/en/2.2.x/tutorial/deploy/#configure-the-secret-key) for deployment. Default, `dev`, is not suitable |
| `check_IP=12` | Interval (hours) for checking / updating the home IP address, `12` hr default. Specify as integer, or `0` to disable |
| `check_Log=3` | Interval (hours) for checking / parsing the Log Files, `3` hr default. Specify as integer, or `0` to disable  |
| **volumes**  | <br> |
| `/path/to/log_directory:`<br>`/path/in/container` | Add log files, fail2ban jail, and MaxMindDB to container, to be read by **BeatLog**. See [data sources](#data-sources) below |
| `/swag_config/<subdirectory>:`<br>`/import/<subdirectory>` | example for SWAG structure in [setup guide](/docs#data-sources) |
| <br> | <br> |
| <br> | <br> |
| **postgres db ports**  | <br> |
| `5432:5432` | Default database port. If the external port is changed, then `db_port` must be specifed for the beatlog container |
| **postgres db environment**  | <br> |
| `POSTGRES_USER=beatlog` | If changed from `beatlog`, `db_user` and `db_database` must be specified for the beatlog container |
| `POSTGRES_PASSWORD=changeme` | PostgreSQL database password, should match `db_password` |
| `TZ=Pacific/Galapagos` | See above |
| **postgres db volumes**  | <br> |
| `/path_to/beatlog_conifg/db:`<br>`/var/lib/postgresql/data` | *[Recommended](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)*: Store database files in a location of your choosing. Facilitates PostgreSQL [updates](/docs/Installation/Installation_Extras.md#postgresql-updates). |

</details>

See the [Installation Extras](/docs/Installation/Installation_Extras.md#beatlog-installation-options) page for more, including how to add healthchecks to the docker containers and how to update the database.

### Data Sources

**BeatLog** reads the following files for the information described. 
See the [Parsing](/docs#parsing) and [Processed Data](/docs#processed-data) sections of the **[Guide](/docs#setup-guide-contents)** for more information.

- **NGINX reverse proxy**
	- access.log - *client requests to the server*
	- error.log - *client request errors and associated severity levels*
- **fail2ban**
	- fail2ban.log - *all activity of fail2ban service, relevant information is parsed and the rest ignored*
	- jail.local - *fail2ban settings and activated filters, checks ignored IPs*
- **MaxMindDB**
	- GeoLite2-City.mmdb - *database to match IP addressess to locations, updated twice monthly*


## Application Setup

Create the container, monitor logs for proper startup, and then navigate to the WebUI at the port specified `http://<your-ip>:5000`. 
*If a database connection error is presented, check the parameters provided in your compose file and consult the container logs for more information.*

### [Setup Guide](/docs#setup-guide-contents)

Get the most information from BeatLog following these steps (detailed in Setup Guide):

1. Specify **[Log File](/docs#log-files)** locations `*/Logs/add/`
2. [Load default **regex methods**](/docs#regex-methods) or create and test your own `*/Logs/add_regex/`
3. [Associate **regex methods**](/docs#adding-regex-to-logs) with **Log Files** to prepare for parsing `*/Logs/<log_file>/regex/`
4. Specify fail2ban **[jail.local](/docs#fail2ban-jail)** location `*/jail/`
5. Specify MaxMind **[GeoLite2-City](/docs#maxminddb)** database location, in **geography settings** `*/settings#geography`
6. Add a user-agent for the **[Nominatim API](/docs#maxminddb)** to fill unnamed locations, in **geography settings**
7. [Parse](/docs#parsing) Logs! [Schedule](/docs#scheduled-tasks) parsing!

## Development

### [Submit](https://github.com/NBPub/BeatLog/issues/new) bugs or feedback.

### In Progress, alpha-0.1.6

[Details](/docs/Installation/Changelog.md#pre-alpha-017-details), [Previous Versions](#pre-release-changelog)

- Documentation ***Proofreading In Progress***
  - ~~planning to move certain sections to their own files, as the "main" README and "docs" README are quite large now~~
  - ~~will update Contents sections to include external links~~
  - ~~will likely break a lot of existing links in the process~~
- Features
  - API v1 fixes/improvements
    - no longer rounding date_spec for [bandwidth](/docs/Features/API.md#bandwidth) API calls to nearest day
	- added [home_ip check](/BeatLog/ops_log.py#L89) before data summary call, added SQL transaction surrounding home_ip calls in general to fix some bugs
	- more?
      - handle geography data better / provide calls to retrieve geography data
	  - other ideas [listed](/docs/Features/API.md#more) on page?
  - Failed Regex
    - if primary and secondary regex methods fail during parsing, line saved to database
	- expanded failed regex page: view lines by log, delete saved lines
- Bug Fixes / Minor Improvements
  - various aesthetic / navigation improvements
  - removed unusued template(s)
  

### Possible Improvements

<details><summary>show/hide</summary>

- Development
  - utilize row factories with psycopg to make cleaner database selections
  - use template file for SQL commands to clean up code
  - add tests for code
  - consider smarter way to gather regex methods across functions
  - solve possible issues with SQL creation: [Home Ignores](/docs/Features/Report.md#home-ignorable)
- Features
  - visitor maps, pan to location from table entry
  - fail2ban filter testing
  - allow for SSL in deployment, *likely just changes to Gunicorn start command*
    - Copy to clipboard button won't work in most browsers without connecting **BeatLog** as `localhost` or adding a certificate for LAN connections.
	- Enable via environmental variable, if enabled Gunicorn should look for cerificates / keyfiles. This way a key can be added and "activated" after initial setup.
	- ***Even with a certificate, BeatLog should only be hosted on trusted network and accessed locally***
</details>


### Pre-Release Changelog

**[Version-by-version details](/docs/Installation/Changelog.md#beatlog-changelog)**

| Version ([Docker Hub](https://hub.docker.com/r/nbpub/beatlog/tags)) | Notes |
| :----: | --- |
| alpha-0.1.0 | Initial release, testing docker deployment. Flask App environmental variables must be used with this image, similar to Local Installation. Internal port is `5000` for this container. |
| alpha-0.1.1 | Switched WSGI from **Werkzeug** to **Gunicorn**, updated compose example. Minor fixes / tweaks. Working to properly implement Gunicorn, APScheduler, psycopg3 together. |
| alpha-0.1.1t | `NullConnectionPool` version of alpha-0.1.1. may be more stable and less load on postgresql, might be slower. ***psycogp3** [ConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#connection-pools) vs. [NullConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools)* |
| alpha-0.1.2, alpha-0.1.2t | Improved contruction of SQL queries across all functions and pages, with care for [SQL Injection risks](https://www.psycopg.org/psycopg3/docs/basic/params.html#danger-sql-injection). Docker images built via Github [workflow](/actions/workflows/main.yml). Added [demo page](https://nbpub.github.io/BeatLog/). Bugfixes and improvements. |
| alpha-0.1.3, alpha-0.1.3t | **BREAKING: altered database schema! [notes](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2).**<br><br> Added **DB Query** and **View** [pages](/docs/Features/Database.md#database-explorer) to access database within BeatLog. Improved handling of **Known Devices.** Added location fill to scheduled log parsing. Bugfixes and improvements. Last NullConnectionPool release. |
| alpha-0.1.4 | Removed support for unauthorized log, [link for migration](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3). Added simple [API](/docs/Features/API.md#simple-json-api).<br><br>No more NullConnectionPool tag. All docker images built and pushed via github actions now. |
| alpha-0.1.5 | Additional API features, and API code organization. Bugfixes / aesthetic improvements. Expanding API documentation and help page. |
| alpha-0.1.6 | **BIG** documentation reorganization.<br>Modified bandwidth API, no longer rounding to nearest day. |

### Other Pages

 - **[Local Installation]**
 - **[Null Connection Pool](/docs/Installation/NullConnectionPool.md#background)**
 - **[Releases](https://github.com/NBPub/BeatLog/releases)**