# BeatLog Changelog

*Latest Version*: alpha-0.1.6

**Stable Version**: alpha-0.1.5

[Repository](/README.md), [Releases](https://github.com/NBPub/BeatLog/releases)

## Contents

- [Pre-Release](pre-release)
  - *[alpha-0.1.6](#pre-alpha-017-details)*
  - **[alpha-0.1.5](#pre-alpha-016-details)**
    - [Images, Notes](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.5)
  - [alpha-0.1.4](#pre-alpha-015-details)
    - [Images, Notes](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.4)  
  - [alpha-0.1.3](#pre-alpha-014-details)
    - [Images, Notes, database migrations](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3)  
  - [alpha-0.1.2](#pre-alpha-013-details)
    - [Images, Notes, database migrations](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2)
  - [alpha-0.1.1](#pre-alpha-012-details)


## Pre-Release

BeatLog is still in development. Every version thus far is a "pre-release".

### pre alpha-0.1.7 details

- JSON API
  - no longer rounding *bandwidth* calls to nearest day
  - cleaned up help page
- Failed Regex
  - if primary and secondary regex methods fail during parsing, line saved to database
  - expanded failed regex page: view lines by log, delete saved lines  
- Documentation
  - big reorganization
- Bug Fixes / Minor Improvements
  - various aesthetic / navigation improvements
  - removed unused template(s)


### pre alpha-0.1.6 details

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
  - Updated [Bootstrap](https://getbootstrap.com/docs/) from to 5.3 from 5.2
  - minor fixes


### pre alpha-0.1.5 details

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



### pre alpha-0.1.4 details

<details><summary>═════════</summary>

- Database Schema
  - changed datatypes for Settings > **KnownDevices** and Jail > **IgnoreIPs**
  - Added time interval columns, **Findtime** and **Bantime** to Jail.
  - detailed in [alpha-0.1.2 tag](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.2).**), manual migrations required prior to update
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
    - *need to continue work on *`Known Devices`* and *`Home Ignorable`* [usage](/docs/Features/Report.md#known-devices)*
  - increased gunicorn worker timeout to 60s, from 30s, to allow for long operations
	- Can revert by 
	  - Timechecks in `Parse All`, individual parsing operations
	  - Analyze report generation with profiler for potential improvements
	  - geography [location lookup](/docs/Features/Geography.md#location-lookup) capped to 20 per attempt
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
