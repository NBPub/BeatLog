# BeatLog Changelog

*Latest Version: alpha-0.1.8*

**Stable Version: alpha-0.1.7**

[Releases](https://github.com/NBPub/BeatLog/releases)

## Contents

- [Pre-Release](pre-release)
  - *[alpha-0.1.8](#alpha-018-details)*
  - **[alpha-0.1.7](#alpha-017-details)**
    - [Tagged Release](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.7) +
  - [alpha-0.1.6](#alpha-016-details)
    - [Tagged Release](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.6) +
  - [alpha-0.1.5](#alpha-015-details)
    - [Tagged Release](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.5) +
  - [alpha-0.1.4](#alpha-014-details)
    - [Tagged Release](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.4) +
  - [alpha-0.1.3](#alpha-013-details)
    - [Tagged Release, database migrations](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3) +
  - [alpha-0.1.2](#alpha-012-details)
    - [Tagged Release, database migrations](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2) +
  - [alpha-0.1.1](#alpha-011-details)
  - [alpha-0.1.0](#alpha-010-details) | *Initial Commit*


## Pre-Release

BeatLog is still in development. Every version thus far is a "pre-release".

### alpha-0.1.8 details

***Nothing yet!***

### alpha-0.1.7 details

- Python upgrade to 3.11
- Added to 
  - [Database Clean](/docs/Features/Database.md#database-cleanup), [JSON API](/docs/Features/API.md#python-packages), [Report](/docs/Features/Report.md#overview), [Beat! Button](/docs/Features/Report.md#beat-button)

<details><summary>═════════</summary>

- Python upgrade 3.10 &rarr; 3.11
- aesthetic / navigation improvements / bugfixes
  - Home Page redesign
- Features
  - ability to delete from all logs at once on [database clean](/docs/Features/Database.md#database-cleanup)
  - API [call](/docs/Features/API.md#python-packages) for listing all Python packages
  - [Beat!](/docs/Features/Report.md#beat-button) button now allows GET requests, not just POST. Real links can be used now. Links provided in filtrate table on report
  - clean geography [cache](/docs/Features/Geography.md#data-assessment) faster with adjusted SQL, 100 row size limit for clears in case of timeout
  - [Report](/docs/Features/Report.md#overview) improvements
    - Filtrate IP list/table
	- Action Count table now only unique IPs for **Finds**, **Bans**, **Visitors**
	- SQL queries improved
- Documentation
  - fixed links, changed headings on this page, proofread releases
  
</details>

### alpha-0.1.6 details

- Documentation expansion and reorganization
- Added to [Failed Regex](/docs/Features/Database.md#failed-regex)

<details><summary>═════════</summary>

- JSON API
  - no longer rounding *bandwidth* calls to nearest day
  - cleaned up help page
  - added [home_ip check](/BeatLog/ops_log.py#L89) before data summary call, added SQL transaction surrounding home_ip calls in general to fix some bugs
- Failed Regex
  - if primary and secondary regex methods fail during parsing, line saved to database
  - expanded failed regex page: view lines by log, delete saved lines  
- Documentation
  - big reorganization
  - updated [Docker README](https://hub.docker.com/r/nbpub/beatlog), *last update: alpha-0.1.2*
- Bug Fixes / Minor Improvements
  - various aesthetic / navigation improvements
  - removed unused template(s)
  
</details>

### alpha-0.1.5 details

- Added to API features
- No longer building **latest** image for `armhf` AKA `arm32v7` architectures, will continue building **stable** images
-[Bootstrap](https://getbootstrap.com/docs/) 5.2 &rarr; 5.3

<details><summary>═════════</summary>

- JSON API
  - new feature: **[bandwidth](/docs/Features/API.md#bandwidth)** - returns total bandwidth from access log.
    - filter return by specifying FIELD and VALUE. String matching provided for `tech`,`URL`, and `referrer`
	- optional filter by date with start/stop inputs. only supporting UNIX format for now
	- see documentation (linked above) for more details
  - named only previous feature **[summary](/docs/Features/API.md#data-summary)**. each "feature" on separate URLs.
  - separated code into two files. Additional features can be added to existing blueprint.
    - *future development:* can copy blueprint and establish `API v2` to maintain existing features through unstable releases
- Docker Image Workflows
  - no longer building "latest" image automatically with each commit for `armhf` AKA `arm32v7` architectures, can build on request
  - will continue building "stable" images with each release
- Bugfixes to make a more "stable" release. Various aesthetic / navigation improvements 
  - API bugfixes
  - Updated [Bootstrap](https://getbootstrap.com/docs/) to 5.3 from 5.2
  - minor fixes

</details>

### alpha-0.1.4 details

- Added [JSON API](/docs/Features/API.md#simple-json-api)
- All docker images built via [workflows](https://github.com/NBPub/BeatLog/actions)
  - **stable** / **latest** images now indicate tagged release / latest commit, respectively
- Removed support for **unauthorized.log**  
- *Database changes - removed Unauthorized table*: [migration instructions](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3)

<details><summary>═════════</summary>

- Version Control, Image management
  - renamed existing workflow to build+push docker images with each commit. Tags still same name, `latest`.
  - created additional workflow to build+push docker images with each release. Tags will be version `alpha-0.1.4` and `stable`.  
  - No more docker images built+pushed by me, all from within Github.
- Code Cleaning
  - removed unauthorized.log support. removed comment blocks for NullConnectionPool versions (see [changes](/docs/Installation/NullConnectionPool.md#background)).
- API v1
  - JSON API to retrieve basic stats, [help page](/docs/Features/API.md#simple-json-api)
- Bug Fixes / Minor Improvements
  - fixed issues with changed code for fail2ban jail page, Known Device settings
  - added check for existing data before API calls
  - various aesthetic / navigation improvements


</details>

### alpha-0.1.3 details

- New [Database features](/docs/Features/Database.md#database-features-documentation), query table data directly via BeatLog
- SQL query creation improved
- *Database changes - Settings table datatypes*: [migration instructions](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2)

<details><summary>═════════</summary>

- Database Schema
  - changed datatypes for Settings &rarr; **KnownDevices** and Jail &rarr; **IgnoreIPs**
  - Added time interval columns, **Findtime** and **Bantime** to Jail.
  - detailed in [alpha-0.1.2 tag](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2), manual migrations required prior to update
- DB Features
  - [page](/docs/Features/Database.md#query) to query database (access, error, fail2ban logs) and [page](/docs/Features/Database.md#results) to view time-ordered results as table
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

### alpha-0.1.2 details

- Docker images built via [workflows](https://github.com/NBPub/BeatLog/actions) with each commit
  - named releases built manually
- First [tagged](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2) release
- Last NullConnectionPool release! [Notes](/docs/Installation/NullConnectionPool.md)

<details><summary>═════════</summary>

- Installation, Docker Compose *Instructions*
  - mount directories instead of files to update logs within **BeatLog** container
  - PostgreSQL upgrade
- Docker Image
  - Build **latest** and **arm32v7-latest** tags via Github [workflow](https://github.com/NBPub/BeatLog/actions)
  - NullConnectionPool versions uploaded manually, may stop later
- Documentation
  - [demonstration page](https://nbpub.github.io/BeatLog/) for Map and Report, added links to docs
- General
  - SQL query creation improved, as per [psycopg3 docs](https://www.psycopg.org/psycopg3/docs/basic/params.html)
    - *need to continue work on *`Known Devices`* and *`Home Ignorable`* [usage](/docs/Features/Report.md#known-devices)*
  - increased gunicorn worker timeout to 60s, from 30s, to allow for longer operations
	- Can revert by 
	  - Timechecks in `Parse All`, individual parsing operations
	  - Analyze report generation with profiler for potential improvements
  - Bug Fixes / Minor Improvements
    - various errors fixed
    - added data to report tables
    - various aesthetic / navigation improvements

</details>

### alpha-0.1.1 details

- production WSGI: **Gunicorn**
 - related fixes
 
<details><summary>═════════</summary>

- Issue with psycopg3 connection pool not restoring discarded connections. Related to Gunicorn or app design?
  - general issue of `ConnectionPool` with Gunicorn's forked workers. error may be solved: pool opened and checked after fork, before first request.
  - Scheduled tasks created with `gunicorn --preload`, to run with a single Gunicorn worker.
- Modified location city/country set to `None` saved as `NULL` in database.
  - added note to docs about inability to set "None" as a city or country name, due to above. [Sorry!](https://geotargit.com/called.php?qcity=None)
- Fixed possible scheduled `parse_all` duplicate prepared statements error
- Potential Gunicorn worker timeout for parsing or location fill operations
  - limited geofill to maximum of 20 locations at a time (20-25 second operation)
  - could increase `gunicorn --timeout` from default 30 seconds
  - what is upper limit for parsing time?
- change fail2ban lastparsed from last saved line to last read line
- expanded documentation
  - continuous drafting
- add production WSGI server **[Gunicorn](https://gunicorn.org/)**, using 3 workers for now
  
</details>

### alpha-0.1.0 details

- Initialized repository, documentation
- Uploaded **BeatLog** images to [Docker Hub](https://hub.docker.com/r/nbpub/beatlog/tags) with alpha-0.1.0 tag
  
