# BeatLog

## Overview
- [Background](#background)
- [Features](#features)
- [Installation](#installation)
	- [Docker](#docker-compose)
	- [Parameters](#parameters)
	- [Setup](#application-setup)
- [Documentation](#documentation)
- [Screenshots](#screenshots)
- [Feedback](#development)
	- [Upcoming](#planned-improvements)

## Background

BeatLog parses [NGINX](https://www.nginx.com/) reverse proxy and [fail2ban](https://www.fail2ban.org/wiki/index.php/Main_Page) logs into readable tables and reports. 
BeatLog helps assess server traffic and to tailor fail2ban filters.

## Features

BeatLog is a [Python](https://www.python.org/) based [web application](https://flask.palletsprojects.com/), and utilizes a [PostgreSQL](https://www.postgresql.org/) database for storage.
Log files are parsed line-by-line using [regex](https://en.wikipedia.org/wiki/Regular_expression). BeatLog provides default patterns, but each log's regex scheme can be customized.

In addition to parsing data from log files, it categorizes each IP address as coming from "Home" (same IP as server) or "Outside" (anywhere else). 
Location information (coordinates, city, country) can be added to all "Outside" entries, using MaxMind's [GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=en) database 
(SWAG users, see: [mod installation](https://github.com/linuxserver/docker-mods/tree/swag-maxmind)). 
If only coordinates are provided from the MaxMind database, locations can be ascertained using the [Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/) reverse geocoding API, 
based on [OpenStreetMap](https://www.openstreetmap.org/about) data.

### Report

A "recent report" synthesizes all log data from the previous few days or a custom date range. 
Charts are integrated using [CanvasJS](https://canvasjs.com/), and [Bootstrap](https://getbootstrap.com/) is used tables for general style.
 - It analyzes both **home** and **outside** connections against fail2ban **finds, bans,** and **ignores** to assess efficacy of [fail2ban filters](https://fail2ban.readthedocs.io/en/latest/filters.html).
 - **Known Devices** can be identified and separated from other outside connections,  
 ex: connections with a [user-agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) of `DSub`, 
 matching requests from a [Subsonic Android app](http://subsonic.org/pages/apps.jsp#dsub).

### Map

Visitor locations can be visualized on an interactive map using [LeafletJS](https://leafletjs.com/) and OpenStreetMap [tiles](https://operations.osmfoundation.org/policies/tiles/).

## Installation

BeatLog is available as [docker images](https://hub.docker.com/r/nbpub/beatlog/tags) in following architectures. 

| Architecture | Note |
| :----: | --- |
| x86-64 | *latest tag* |
| arm64 | *latest tag*  |
| armhf | *special tag required* |

A PostgreSQL database is required, and can be included in the same docker deployment, as shown in the examples.
Or, connect to an existing database (ignore `depends_on:` and following lines), by providing the proper connection parameters are provided under `environment:`.

Logs and other files are added to the container via [volumes](https://docs.docker.com/storage/volumes/). 
In the example below, they will be available in the `/import` directory.

The `healthcheck:` is optional. The [parameters](#parameters) are detailed in the next section.

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
      - check_IP=12
      - check_Log=3	  
    volumes:
      - /path_to/swag_config/log/nginx/access.log:/import/access.log:ro  
      - /path_to/swag_config/log/nginx/error.log:/import/error.log:ro
      - /path_to/swag_config/log/nginx/unauthorized.log:/import/unauthorized.log:ro
      - /path_to/swag_config/log/fail2ban/fail2ban.log:/import/fail2ban.log:ro
      - /path_to/swag_config/fail2ban/jail.local:/import/jail.local:ro 
      - /path_to/swag_config/geoip2db/GeoLite2-City.mmdb:/import/GeoLite2-City.mmdb:ro
  healthcheck:
      test: curl -I --fail http://localhost:5000 || exit 1
      interval: 300s
      timeout: 10s
      start_period: 20s
    restart: unless-stopped
    depends_on:
      - db
  db:
    image: postgres:latest
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
| `db_host=<IP>` | IP address of PostgreSQL database, defaults to `localhost` which may fail |
| `db_password=changeme` | PostgreSQL database password, should match `POSTGRES_PASSWORD` |
| `db_port=` | Only needed if **database port** is changed |
| `db_user=` | Only needed if `POSTGRES_USER` is changed |
| `db_database=` | Only needed if `POSTGRES_USER` is changed |
| `FLASK_SECRET_KEY=<secretkey>` | Generate a secret key for deployment. Default, `dev`, is not suitable |
| `check_IP=12` | Interval (hours) for checking / updating the home IP address. Specify as integer, or 0 to disable |
| `check_Log=3	` | Interval (hours) for checking / parsing the Log Files. Specify as integer, or 0 to disable  |
| **volumes**  | ---- |
| `/path/to/file=/path/in/container:ro` | Add log files, fail2ban jail, and MaxMindDB to container as read-only volumes. |
| **db ports**  | ---- |
| `5432:5432` | Default database port. If the external port is changed, then `db_port` must be specifed for the beatlog container |
| **db environment**  | ---- |
| `POSTGRES_USER=beatlog` | Defaults to beatlog. If changed, `db_user` and `db_database` must be specified for the beatlog container |
| `POSTGRES_PASSWORD=changeme` | PostgreSQL database password, should match `db_password` |
  

### Docker [CLI](https://docs.docker.com/engine/reference/commandline/cli/)

*to be added*
```bash
docker run -d \
```

### Application Setup

Create the container and then navigate to the WebUI at `http://<your-ip>:5000`. If a database connection error is presented, check the parameters provided in your compose file.

Get the most information from BeatLog following these steps:

1. Specify **Log File** locations `/Logs/add/`
2. Load default **regex methods** or create and test your own `/Logs/add_regex/`
3. Associate **regex methods** with **Log Files** to prepare for parsing `/Logs/<log_file>/regex/`
4. Specify fail2ban **jail.local** location `/home/jail/`
5. Specify MaxMind **GeoLite2-City** database location, in **geography settings** `/home/settings#geography`
6. Add a user-agent for the **Nominatim API** to fill unnamed locations, in **geography settings**
7. Parse Logs!

## Documentation

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

If you are using [SWAG](https://github.com/linuxserver/docker-swag) for your reverse proxy, the above files live in the following structure. 
These relative paths are demonstrated as volumes in the provided [Docker Compose example](#docker-compose).

```
SWAG Config
│
└───log
│   │
│   └───fail2ban
│   │    │   fail2ban.log
│   │      
│   └───nginx
│   │    │   access.log
│   │    │   error.log
│   │    │   unauthorized.log
│   │    │   ...  
│   │   ...
│ 
└───fail2ban 
│   │   jail.local
│   │   ...
│
└───geoip2db
│   │   GeoLite2-City.mmdb 
│ ...
```

## Development

Submit bugs or feedback here.

### Planned Improvements

- expand documentation
- pan to location feature for maps (table links)
- add tests for code
- asyncio for scheduled tasks and/or other routines
- utilize row factories with psycopg to make cleaner database selections
- use template file for SQL commands to clean up code
- consider smarter way to gather regex methods across functions


