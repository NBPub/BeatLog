# <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> BeatLog 


## Overview
- [Background](#background)
- [Features](#features)
- [Installation](#installation)
	- [Docker](#docker-compose)
	- [Parameters](#parameters)
	- [Setup](#application-setup)
- [Documentation](#documentation)
	- [Data Sources](#data-sources)
	- [Processed Data](#processed-data)
- [Feedback](#development)
	- [Upcoming](#planned-improvements)

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

See the [documentation](/docs) for a full list of features. The **Report** and **Visitor Map** are highlighted here.

### Report

A "recent report" synthesizes all log data from the previous few days or a custom date range. 
Charts are integrated using [CanvasJS](https://canvasjs.com/), and [Bootstrap](https://getbootstrap.com/) is used for tables and styling.
 - Analyze **home** and **outside** connections against fail2ban **finds, bans,** and **ignores** to assess efficacy of [fail2ban filters](https://fail2ban.readthedocs.io/en/latest/filters.html).
 - Scrutinize traffic from frequent visitors, monitor popular client requests
 - **Known Devices** can be identified and separated from other outside connections, for example
 connections with a [user-agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) of `DSub`, 
 matching requests from a [Subsonic Android app](http://subsonic.org/pages/apps.jsp#dsub), may be excluded.
 - [Details and screenshots](/docs#report)

### Visitor Map

Visitor locations can be visualized on an interactive map using [LeafletJS](https://leafletjs.com/) and OpenStreetMap [tiles](https://operations.osmfoundation.org/policies/tiles/). 
 - Location markers are scaled by total connections or unique visitors (IPs) over the time range.
 - [Details and screenshots](/docs#visitor-map)

## Installation

BeatLog is available as [docker images](https://hub.docker.com/r/nbpub/beatlog/tags) in the following architectures. 

| Architecture | Tag |
| :----: | --- |
| x86-64 | *latest* |
| arm64 | *latest*  |
| armhf | *arm32v7-latest* |

A PostgreSQL database is required, and can be included in the same docker deployment, as shown below.
Or, connect to an existing database, by providing connection settings under `environment:`. 

Logs and other files are added to the container via [volumes](https://docs.docker.com/storage/volumes/). 
In the example below, they will be available in the `/import` directory.

The [parameters](#parameters) are detailed in the next section. Optional `healthcheck` and `adminer` additions are shown [below](#extra-options).

*With existing database,* `depends_on:` *and the following lines are not needed.*

### Docker [Compose](https://docs.docker.com/compose/)

```yaml
---
version: "2.1"
services:
  beatlog:
    image: nbpub/beatlog:latest
    container_name: beatlog
    ports:
      - 5000:5000
    environment:
      - TZ=America/Los_Angeles
      - db_host=<IP>
      - db_password=changeme	  
      - FLASK_SECRET_KEY=<secretkey>
      - FLASK_APP=beatlog
      - FLASK_RUN_HOST=0.0.0.0  
      - check_IP=12
      - check_Log=3	  
    volumes:
      - /path_to/swag_config/log/nginx/access.log:/import/access.log:ro  
      - /path_to/swag_config/log/nginx/error.log:/import/error.log:ro
      - /path_to/swag_config/log/nginx/unauthorized.log:/import/unauthorized.log:ro
      - /path_to/swag_config/log/fail2ban/fail2ban.log:/import/fail2ban.log:ro
      - /path_to/swag_config/fail2ban/jail.local:/import/jail.local:ro 
      - /path_to/swag_config/geoip2db/GeoLite2-City.mmdb:/import/GeoLite2-City.mmdb:ro
    depends_on:
      - db
  db:
    image: postgres
    ports:
      - 5432:5432
    environment:
      - POSTGRES_USER=beatlog
      - POSTGRES_PASSWORD=changeme
    restart: unless-stopped   	
```

### Parameters 

Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate `<external>:<internal>` respectively. 
For example, setting ports to `5001:5000` would expose port `5000` from inside the container to be accessible from the host's IP on port `5001` outside the container.

| Parameter | Function |
| :----: | --- |
| **ports** | ---- |
| `5000:5000` | Default Flask port. Internal port should not be changed. |
| **environment**  | ----  |
| `TZ=America/Los_Angeles` | Timezone should match that of reverse proxy. Defaults to `UTC`. [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `db_host=<IP>` | IP address or host name of PostgreSQL database, defaults to `localhost` which may fail |
| `db_password=changeme` | PostgreSQL database password, should match `POSTGRES_PASSWORD` |
| `db_port=` | Only needed if **database port** is changed |
| `db_user=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `db_database=` | Only needed if `POSTGRES_USER` is changed, defaults to `beatlog` |
| `FLASK_SECRET_KEY=<secretkey>` | Generate a secret key for deployment. Default, `dev`, is not suitable |
| `FLASK_APP=beatlog` | Needed for container startup |
| `FLASK_RUN_HOST=0.0.0.0` | Allows access to BeatLog across the local network |
| `FLASK_RUN_PORT=5000` | Only needed if internal port is changed, see above |
| `check_IP=12` | Interval (hours) for checking / updating the home IP address. Specify as integer, or 0 to disable |
| `check_Log=3` | Interval (hours) for checking / parsing the Log Files. Specify as integer, or 0 to disable  |
| **volumes**  | ---- |
| `/path/to/file=/path/in/container:ro` | Add log files, fail2ban jail, and MaxMindDB to container as read-only volumes. |
| | |
| **postgres db ports**  | ---- |
| `5432:5432` | Default database port. If the external port is changed, then `db_port` must be specifed for the beatlog container |
| **postgres db environment**  | ---- |
| `POSTGRES_USER=beatlog` | If changed from `beatlog`, `db_user` and `db_database` must be specified for the beatlog container |
| `POSTGRES_PASSWORD=changeme` | PostgreSQL database password, should match `db_password` |
  

### Extra Options

- Add a [healthcheck](https://docs.docker.com/engine/reference/builder/#healthcheck) to your docker-compose to indicate container status.

<details><summary>Healthcheck</summary>

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
      test: curl -I --fail http://localhost:5000 || exit 1
      interval: 300s
      timeout: 10s
      start_period: 20s
    .
    .
    .
```
</details>

- Add an [Adminer](https://www.adminer.org/) container to interact with your database. Database adjustments outside **BeatLog** are not supported and could break functionality. 

<details><summary>Adminer</summary>

```yaml
    .
    .
    .
  db:
    .
    .
    .
  adminer:
    image: adminer
    restart: unless-stopped
    ports:
      - 8080:8080
```
</details>

### Application Setup

Create the container and then navigate to the WebUI at `http://<your-ip>:5000`. If a database connection error is presented, check the parameters provided in your compose file. 
**[Setup Guide](/docs#setup)**

Get the most information from BeatLog following these steps:

1. Specify **Log File** locations `*/Logs/add/`
2. Load default **regex methods** or create and test your own `*/Logs/add_regex/`
3. Associate **regex methods** with **Log Files** to prepare for parsing `*/Logs/<log_file>/regex/`
4. Specify fail2ban **jail.local** location `*/home/jail/`
5. Specify MaxMind **GeoLite2-City** database location, in **geography settings** `*/home/settings#geography`
6. Add a user-agent for the **Nominatim API** to fill unnamed locations, in **geography settings**
7. Parse Logs!

## Documentation

Setup guide for **BeatLog** and more on features live [here](/docs#setup).

### Data Sources

The following files provide information for BeatLog to generate reports and maps:

- **NGINX**
	- access.log - *client requests to the server*
	- error.log - *various issues and associated severity levels*
	- unauthorized.log - *redundant to **access.log**, captures requests with [401 HTTP status codes](https://www.httpstatuses.org/401)*
- **fail2ban**
	- fail2ban.log - *all activity of fail2ban service, relevant information is parsed and the rest ignored*
	- jail.local - *fail2ban settings and activated filters, checks whether "home" IP is ignored*
- **MaxMindDB**
	- GeoLite2-City.mmdb - *database to match IP addressess to locations, updated twice monthly*


### Processed Data

The following tables describe how parsed logs and other data are saved into the database. 
See [PostgreSQL docs](https://www.postgresql.org/docs/current/datatype.html) for more information on data types. 
The [Mozilla HTTP docs](https://developer.mozilla.org/en-US/docs/Web/HTML) are a good reference for learning more about each parameter, and are linked where column names are ambiguous.

Wikipedia has a nice [example](https://en.wikipedia.org/wiki/Common_Log_Format#Example) of the **Common Log Format** in its article.

#### Access / Unauthorized Logs

*home and geo are not directly read from the log file*

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, one second resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Method** | text | HTTP request [method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) |
| **URL** | text | Component of resource requested by client |
| **HTTP** | integer | HTTP [network protocol](https://developer.mozilla.org/en-US/docs/Glossary/HTTP_2), typically **2** or **1.1**. It is multiplied by 10 to save as an integer. |
| **Status** | integer | HTTP status [code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), see [here](https://www.httpstatuses.org/) for a handy list of codes and their descriptions. |
| **Bytes** | integer | Size of object returned to the client |
| **Referrer** | text | Component of resource requested by client, more info and note on spelling issues [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referer) |
| **Tech** | text | [User-Agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) HTTP request header. Useful for identifying Known Devices. |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |


#### Error Log

*home and geo are not directly read from the log file*

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, one second resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Level** | text | Log level, or measure of severity. See [here](https://nginx.org/en/docs/ngx_core_module.html#error_log) for more info. |
| **Message** | text | Contents of error message |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |


#### fail2ban Log

*home and geo are not directly read from the log file*

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, millisecond resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Filter** | text | fail2ban filter doing the action |
| **Action** | text | fail2ban action, only **Finds**, **Bans**, and **Ignores** are saved. |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |

#### Geography

| Column | Data Type | Description |
| :----: | --- | --- |
| **coords** | \[integer,integer\] | Coordinates provided by MaxMindDB. They are multiplied by **1E4** to save as integers. |
| **city** | text | City name (en) from MaxMindDB or closest name match from Nominatim API |
| **country** | text | Country name (en) from MaxMindDB or from Nominatim API |

## Development

[Submit](https://github.com/NBPub/BeatLog/issues/new) bugs or feedback.

### Planned Improvements

- expand documentation 
  - *in progress*
- add production WSGI server
- Github workflow for publishing Docker images
- pan to location feature for maps (table links)
- add tests for code
- asyncio for scheduled tasks and/or other routines
- utilize row factories with psycopg to make cleaner database selections
- use template file for SQL commands to clean up code
- consider smarter way to gather regex methods across functions

### Local Installation - Python venv

- *Required: connectable postgresql database*
- Add **[BeatLog folder](https://github.com/NBPub/BeatLog/tree/main/BeatLog)** and **[requirements.txt](https://github.com/NBPub/BeatLog/blob/main/requirements.txt)** into a new directory
- Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
- Install requirements `pip install -r requirements.txt`
- Create and populate a **.env** file, model after docker-compose [example](#docker-compose)
- Run flask app `flask run` or in debug mode `flask --debug run`

See the Flask [Installation](https://flask.palletsprojects.com/en/2.2.x/installation/) and [Quickstart](https://flask.palletsprojects.com/en/2.2.x/quickstart/) docs for details on these steps.
